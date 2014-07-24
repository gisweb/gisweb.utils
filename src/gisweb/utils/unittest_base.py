#!../../../../../bin/zopepy
# -*- coding: utf-8 -*-

"""
Tests in this section only needs zopepy environment.
"""

import unittest

class Test_anagrafica_utils(unittest.TestCase):

    def test_cf_build(self):
        from gisweb.utils import cf_build
        result = cf_build('Rocca', 'Emanuele', 1983, 11, 18, 'M', 'D969')
        self.assertEqual(result, "RCCMNL83S18D969H")

    def test_1_is_valid_cf(self):
        from gisweb.utils import is_valid_cf
        result = is_valid_cf("RCCMNL83S18D969H")
        self.assertTrue(result)

    def test_2_is_valid_cf(self):
        from gisweb.utils import is_valid_cf
        result = is_valid_cf("RCCMNL83S18D969X")
        self.assertFalse(result)

    def test_3_is_valid_cf(self):
        from gisweb.utils import is_valid_cf
        result = is_valid_cf("RCCMNL83S18D969X", validate=False)
        self.assertEqual(result, "H")

    def test_is_valid_piva(self):
        from gisweb.utils import is_valid_piva
        result = is_valid_piva("01533090997")
        self.assertTrue(result)


class Test_gpolyencode_utils(unittest.TestCase):

    def test_gpoly_encode(self):
        try:
            import gpolyencode
        except ImportError:
            result = True
        except:
            raise
        else:
            from gisweb.utils import decode_line, gpoly_encode
            encoded_points = "grkyHhpc@B[[_IYiLiEgj@a@q@yEoAGi@bEyH_@aHj@m@^qAB{@IkHi@cHcAkPSiMJqEj@s@CkFp@sDfB}Ex@iBj@S_AyIkCcUWgAaA_JUyAFk@{D_]~KiLwAeCsHqJmBlAmFuXe@{DcByIZIYiBxBwAc@eCcAl@y@aEdCcBVJpHsEyAeE"
            latlon = decode_line(encoded_points)
            lonlat = decode_line(gpoly_encode(latlon).get('points'))
            is_almost_equal = lambda x,y: abs(x-y)<.0001
            test = lambda pair: is_almost_equal(pair[0][0], pair[1][1]) and is_almost_equal(pair[0][1], pair[1][0])
            result = all(map(test, zip(latlon, lonlat)))
        self.assertTrue(result)

class Test_url_utils(unittest.TestCase):

    def test_wsquery(self):
        from gisweb.utils import wsquery
        result = wsquery('http://localhost')['status_code']
        self.assertTrue(result>=0)

class Test_plomino_utils(unittest.TestCase):
    """ """

    def test_StartDayofMonth(self):
        from Products.CMFPlomino.PlominoUtils import StringToDate
        in_date = StringToDate('2000.05.05', '%Y.%m.%d')
        expected = StringToDate('2000.05.01', '%Y.%m.%d')
        result = StringToDate('2000.05.01', '%Y.%m.%d')
        self.assertEqual(expected, result)

    def test_LastDayofMonth(self):
        from gisweb.utils import LastDayofMonth
        from Products.CMFPlomino.PlominoUtils import StringToDate
        in_date = StringToDate('2000.05.05', '%Y.%m.%d')
        expected = StringToDate('2000.06.01', '%Y.%m.%d')-1
        result = LastDayofMonth(in_date)
        self.assertEqual(expected, result)

    def test_addToDate(self):
        from gisweb.utils import addToDate
        from Products.CMFPlomino.PlominoUtils import StringToDate
        in_date = StringToDate('2000.05.05', '%Y.%m.%d')
        result = addToDate(in_date, 2, units='months', start=1)
        expected = StringToDate('2000.07.04', '%Y.%m.%d')
        self.assertEqual(expected, result)

    def test_guessType(self):
        from gisweb.utils import guessType
        htmlcontent = """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN"
"http://www.w3.org/TR/html4/strict.dtd">
<html>
  <head>
    <title>Page title</title>
  </head>
  <body>
  </body>
</html>"""
        result = guessType(htmlcontent, 'plain.html')['contenttype']
        self.assertEqual('text/html', result)

if __name__ == "__main__":
    unittest.main()
