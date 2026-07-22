using FWO.Data.Report;
using FWO.Report.Filter;
using NUnit.Framework;
using System.Reflection;
using System.Text.RegularExpressions;

namespace FWO.Test
{
    [TestFixture]
    [Parallelizable]
    public class DynGraphqlQueryTest
    {
        private static string InvokeGetDevWhereFilter(DeviceFilter? deviceFilter)
        {
            MethodInfo method = typeof(DynGraphqlQuery).GetMethod("GetDevWhereFilter", BindingFlags.NonPublic | BindingFlags.Static)
                ?? throw new MissingMethodException(nameof(DynGraphqlQuery), "GetDevWhereFilter");
            return (string)method.Invoke(null, [deviceFilter])!;
        }

        private static string Normalize(string query)
        {
            return Regex.Replace(query, "\\s+", " ", RegexOptions.None, TimeSpan.FromMilliseconds(1000)).Trim();
        }

        [Test]
        public void GetDevWhereFilter_OnlyIncludesSelectedDevices_WithOrSeparatorsBetweenEntries()
        {
            DeviceFilter deviceFilter = new(
            [
                new ManagementSelect
                {
                    Id = 1,
                    Devices =
                    [
                        new DeviceSelect { Id = 5, Selected = true },
                        new DeviceSelect { Id = 6, Selected = false }
                    ]
                },
                new ManagementSelect
                {
                    Id = 2,
                    Devices =
                    [
                        new DeviceSelect { Id = 9, Selected = true }
                    ]
                }
            ]);

            string result = Normalize(InvokeGetDevWhereFilter(deviceFilter));

            Assert.That(result, Does.Contain("_or: [{ dev_id: {_eq:5 } }, { dev_id: {_eq:9 } }]"));
            Assert.That(result, Does.Not.Contain("dev_id: {_eq:6 }"));
        }
    }
}
