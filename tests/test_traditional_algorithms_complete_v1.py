import unittest

from upstream_adapters.complete import bazi_complete, liuyao_complete


class TraditionalCompleteTests(unittest.TestCase):
 def test_complete_profiles_are_research_only(self):
    structure={
      "year":{"stem":"甲","branch":"子","ten_god_stem":"比肩","ten_gods_hidden":["正印"]},
      "month":{"stem":"丙","branch":"午","ten_god_stem":"食神","ten_gods_hidden":["食神"]},
      "day":{"stem":"甲","branch":"寅","ten_god_stem":"比肩","ten_gods_hidden":["比肩"]},
      "time":{"stem":"庚","branch":"申","ten_god_stem":"七杀","ten_gods_hidden":["七杀"]}}
    result=bazi_complete(structure,"甲",None)
    self.assertEqual(result["review_status"],"UNCONFIRMED")
    self.assertFalse(result["production_activatable"])
    self.assertTrue(result["strength"]["support_units"] and result["strength"]["counter_units"])


 def test_liuyao_general_question_does_not_hide_yongshen_choice(self):
    chart={"primary":{"lines":[],"shi_position":1,"ying_position":4},"changed":None,"moving_lines":[]}
    result=liuyao_complete(chart,{"question_type":"general_trend"})
    self.assertEqual(result["question"]["status"],"insufficient")
    self.assertEqual(result["verdict"],"insufficient")


if __name__=="__main__": unittest.main()
