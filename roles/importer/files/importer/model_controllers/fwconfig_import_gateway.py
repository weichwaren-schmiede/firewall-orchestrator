import traceback
from typing import Any

import fwo_const
from fwo_api import FwoApi
from fwo_exceptions import FwoImporterError
from fwo_log import FWOLogger
from model_controllers.rulebase_link_controller import RulebaseLinkController
from models.rulebase_link import (  # TODO: check if we need RulebaseLinkUidBased as well
    RulebaseLink,
    RulebaseLinkUidBased,
)
from services.global_state import GlobalState
from services.service_provider import ServiceProvider
from services.uid2id_mapper import Uid2IdMapper


class FwConfigImportGateway:
    """
    Provides methods import gateway information into the FWO API.
    """

    _global_state: GlobalState
    _uid2id_mapper: Uid2IdMapper
    _rb_link_controller: RulebaseLinkController

    def __init__(self):
        service_provider = ServiceProvider()
        self._global_state = service_provider.get_global_state()
        self._uid2id_mapper = service_provider.get_uid2id_mapper(self._global_state.import_state.state.import_id)
        self._rb_link_controller = RulebaseLinkController()

    def get_rb_link_controller(self) -> RulebaseLinkController:
        return self._rb_link_controller

    def get_global_state(self) -> GlobalState:
        return self._global_state

    def update_gateway_diffs(self):
        # add gateway details:
        self._rb_link_controller.get_rulebase_links(
            self._global_state.import_state.state, self._global_state.import_state.api_call
        )
        if (
            self._global_state.import_state.state.is_clearing_import
            and self._global_state.normalized_config is not None
            and len(self._global_state.normalized_config.gateways) == 0
        ):
            removed_link_ids = [link.id for link in self._rb_link_controller.rb_links if link.id is not None]
            self._rb_link_controller.remove_rulebase_links(
                self._global_state.import_state.api_call,
                self._global_state.import_state.state.stats,
                self._global_state.import_state.state.import_id,
                removed_link_ids,
            )
            self.update_interface_diffs()
            self.update_routing_diffs()
            return
        required_inserts, required_removes = self.update_rulebase_link_diffs()
        self._rb_link_controller.insert_rulebase_links(
            self._global_state.import_state.api_call, self._global_state.import_state.state.stats, required_inserts
        )
        self._rb_link_controller.remove_rulebase_links(
            self._global_state.import_state.api_call,
            self._global_state.import_state.state.stats,
            self._global_state.import_state.state.import_id,
            required_removes,
        )
        self.update_interface_diffs()
        self.update_routing_diffs()
        self.update_removed_gateways()

    def update_rulebase_link_diffs(self) -> tuple[list[dict[str, Any]], list[int]]:
        if self._global_state.normalized_config is None:
            raise FwoImporterError("normalized_config is None in update_rulebase_link_diffs")
        if self._global_state.previous_config is None:
            raise FwoImporterError("previous_config is None in update_rulebase_link_diffs")

        required_inserts: list[dict[str, Any]] = []
        required_removes: list[int] = []

        for gw in self._global_state.normalized_config.gateways:
            previous_config_gw = next(
                (p_gw for p_gw in self._global_state.previous_config.gateways if gw.Uid == p_gw.Uid), None
            )

            if gw in self._global_state.previous_config.gateways:
                # this check finds all changes in gateway (including rulebase link changes)
                # gateway found with exactly same properties in previous config
                continue

            FWOLogger.debug(f"gateway {gw!s} NOT found in previous config", 9)
            if gw.Uid is None:
                raise FwoImporterError("found gateway with Uid = None")
            gw_id = self._global_state.import_state.state.lookup_gateway_id(gw.Uid)

            to_remove = list(
                set(previous_config_gw.RulebaseLinks if previous_config_gw else []) - set(gw.RulebaseLinks)
            )

            required_removes.extend(self._get_required_removes(to_remove, gw_id))

            to_add = list(set(gw.RulebaseLinks) - set(previous_config_gw.RulebaseLinks if previous_config_gw else []))

            required_inserts.extend(self._get_required_inserts(to_add, gw_id))

        return required_inserts, required_removes

    def _get_required_inserts(
        self,
        to_add: list[RulebaseLinkUidBased],
        gw_id: int | None,
    ) -> list[dict[str, Any]]:
        inserts: list[dict[str, Any]] = []
        for link in to_add:
            from_rule_id = (
                self._uid2id_mapper.get_rule_id(link.from_rule_uid, before_update=False) if link.from_rule_uid else None
            )
            from_rulebase_id = (
                None
                if link.from_rulebase_uid is None or link.from_rulebase_uid == ""
                else self._uid2id_mapper.get_rulebase_id(link.from_rulebase_uid, before_update=False)
            )
            to_rulebase_id = self._uid2id_mapper.get_rulebase_id(link.to_rulebase_uid, before_update=False)
            link_type_id = self._global_state.import_state.state.lookup_link_type(link.link_type)
            if type(link_type_id) is not int:
                FWOLogger.warning(f"did not find a link_type_id for link_type {link.link_type}")
            if gw_id is None:
                FWOLogger.warning(f"did not find a gwId for UID {link}")
                continue
            inserts.append(
                RulebaseLink(
                    gw_id=gw_id,
                    from_rule_id=from_rule_id,
                    to_rulebase_id=to_rulebase_id,
                    link_type=link_type_id,
                    is_initial=link.is_initial,
                    is_global=link.is_global,
                    is_section=link.is_section,
                    from_rulebase_id=from_rulebase_id,
                    created=self._global_state.import_state.state.import_id,
                ).to_dict()
            )
            FWOLogger.debug(f"link {link} was added", 9)
        return inserts

    def _get_required_removes(
        self,
        to_remove: list[RulebaseLinkUidBased],
        gw_id: int | None,
    ) -> list[int]:
        # For removes we need the old fk ids (before_update=True)
        remove_ids: list[int] = []
        for link in to_remove:
            from_rule_id = (
                self._uid2id_mapper.get_rule_id(link.from_rule_uid, before_update=True) if link.from_rule_uid else None
            )
            from_rulebase_id = (
                None
                if link.from_rulebase_uid is None or link.from_rulebase_uid == ""
                else self._uid2id_mapper.get_rulebase_id(link.from_rulebase_uid, before_update=True)
            )
            to_rulebase_id = self._uid2id_mapper.get_rulebase_id(link.to_rulebase_uid, before_update=True)
            link_type_id = self._global_state.import_state.state.lookup_link_type(link.link_type)
            if type(link_type_id) is not int:
                FWOLogger.warning(f"did not find a link_type_id for link_type {link.link_type}")
            if gw_id is None:
                FWOLogger.warning(f"did not find a gwId for UID {link}")
                continue
            link_dict = RulebaseLink(
                gw_id=gw_id,
                from_rule_id=from_rule_id,
                to_rulebase_id=to_rulebase_id,
                link_type=link_type_id,
                is_initial=link.is_initial,
                is_global=link.is_global,
                is_section=link.is_section,
                from_rulebase_id=from_rulebase_id,
                created=self._global_state.import_state.state.import_id,
            ).to_dict()
            link_in_db = self._try_get_id_based_link(link_dict, self._rb_link_controller.rb_links)
            if link_in_db and link_in_db.id is not None:
                remove_ids.append(link_in_db.id)
        return remove_ids

    def _try_get_id_based_link(self, link: dict[str, Any], link_list: list[RulebaseLink]):
        return next(
            (
                existing_link
                for existing_link in link_list
                if {**existing_link.to_dict(), "created": 0} == {**link, "created": 0}
            ),
            None,
        )

    def update_interface_diffs(self):
        # TODO: needs to be implemented
        pass

    def update_routing_diffs(self):
        # TODO: needs to be implemented
        pass

    def update_removed_gateways(self):
        if self._global_state.normalized_config is None or self._global_state.previous_config is None:
            raise FwoImporterError("normalized_config or previous_config is None in update_removed_gateways")
        gw_uids_to_remove = [
            gw.Uid
            for gw in self._global_state.previous_config.gateways
            if gw.Uid not in [ngw.Uid for ngw in self._global_state.normalized_config.gateways]
        ]

        if not gw_uids_to_remove:
            return  # nothing to do
        gw_ids_to_remove = [
            self._global_state.import_state.state.lookup_gateway_id(gw_uid) for gw_uid in gw_uids_to_remove if gw_uid
        ]

        FWOLogger.info(f"marking all entries associated with gateways {gw_uids_to_remove!s} as removed")
        mutation = FwoApi.get_graphql_code(
            file_list=[fwo_const.GRAPHQL_QUERY_PATH + "device/markGatewaysRemoved.graphql"]
        )
        query_variables = {
            "gwIds": gw_ids_to_remove,
            "importId": self._global_state.import_state.state.import_id,
        }
        try:
            result = self._global_state.import_state.api_connection.call(mutation, query_variables=query_variables)
            affected_tables = {key: value["affected_rows"] for key, value in result["data"].items()}
            FWOLogger.debug(f"marked gateways {gw_uids_to_remove!s} as removed in tables: {affected_tables!s}")
            FWOLogger.info(
                f"marked {sum(affected_tables.values())!s} entries as removed for gateways {gw_uids_to_remove!s}"
            )
            self._global_state.import_state.state.stats.statistics.rulebase_link_delete_count += affected_tables.get(
                "update_rulebase_link", 0
            )
        except Exception:
            FWOLogger.error(
                f"fwconfig_import_gateway - error while marking gateways {gw_uids_to_remove!s} as removed: {traceback.format_exc()!s}"
            )
