from pydantic import BaseModel


# Rule is the model for a normalized rule_metadata
class RuleMetadatum(BaseModel):
    rule_uid: str
    mgm_id: int
    rule_created: int
    rule_last_hit: str | None = None
