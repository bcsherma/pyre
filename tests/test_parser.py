import pyre


def test_parser():
    evr = pyre.EventFileReader(team="SFN", year=2019, league="N")
    evr.data_frame()
