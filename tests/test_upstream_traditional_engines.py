import os
import unittest

from upstream_adapters import BaziUpstreamAdapter, LiuyaoUpstreamAdapter


class UpstreamTraditionalTests(unittest.TestCase):
    def test_bazi_is_mechanical_and_interpretation_is_not_admitted(self):
        result=BaziUpstreamAdapter().execute({"local_date":"1990-01-01","local_time":"12:00:00",
          "method_profile":{"profile_id":"lunar-python-sect1","version":"1.0.0","sect":1,"wall_time_policy":"supplied_local_wall_time"}})
        self.assertEqual(result["output"]["pillars"]["day"],"丙寅")
        self.assertIn("useful_god",result["output"]["not_admitted"])

    def test_liuyao_bottom_to_top_najia_shiying_and_changed(self):
        result=LiuyaoUpstreamAdapter().execute({"lines":[7,8,9,6,7,8],"day_stem_index":0,
          "method_profile":{"profile_id":"yaomancy-liuyao-engine-0.1.0","version":"1.0.0"}})
        self.assertEqual(result["output"]["moving_lines"],[3,4])
        self.assertEqual(len(result["output"]["primary"]["lines"]),6)
        self.assertTrue(any(line["shiying"]=="世" for line in result["output"]["primary"]["lines"]))
        self.assertIsNotNone(result["output"]["changed"])

    def test_input_order_does_not_mutate_canonical_lines(self):
        adapter=LiuyaoUpstreamAdapter()
        first=adapter.execute({"lines":[6,7,8,9,6,7],"day_stem_index":9,"method_profile":{"profile_id":"yaomancy-liuyao-engine-0.1.0","version":"1.0.0"}})
        second=adapter.execute({"method_profile":{"version":"1.0.0","profile_id":"yaomancy-liuyao-engine-0.1.0"},"day_stem_index":9,"lines":[6,7,8,9,6,7]})
        self.assertEqual(first["canonical_hash"],second["canonical_hash"])


if __name__=="__main__": unittest.main()
