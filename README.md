baidutongji
============

A utilities to login to <http://tongji.baidu.com> and grab the first
prevew page data and location data.


Install
-------

```bash
pip install git+git://github.com/TylerTemp/baidutongji.git
```

Usage
---------

### Initialize ###

```python
from baidutongji import BaiduTongji
```

```
BaiduTongji(username, password, site_id, save_image_file='/TMPDIR/validate.png', save_code_file='/TMPDIR/validate')
```

*   `username`: (required) Baidu Tongji username
*   `password`: (required) Baidu Tongji password
*   `site_id`: (required) You site id on Baidu Tongji
*   `save_image_file`: (optional) The path to save the validate image. Use `validate.png` under temp dir by default.
*   `save_code_file`: (optional) The path where `tesseract` save the ORC result, by default it's in `validate`
    (`tesseract` will add `.txt` suffix) under temp dir

### Login ###

```python
from baidutongji import BaiduTongji
l = BaiduTongji(...)
l.pre_login(sleep=1)
```

`.pre_login` will get some cookie and save the validate image. The file path is `save_image_file`
`sleep` can set the sleep time to aviod `RESTful` API explode.


```
l.do_login(code)
```

`.do_login` to login the page. `code` is the validate code.
Return `True` for login success, `False` otherwise.

### Auto Login ###

If you've already install `tesseract` on your computer, you can use `.login`
to auto login.

```python
from baidutongji import BaiduTongji
l = BaiduTongji(...)
while not l.login():    # ORC & try login
    print('retry...')    # failed, re-try
```

### siteid

You site has one or more site ids.

BaiduTongji will set the default site id as your site on Baidu.

You change it by

``` python
>>> l.site_ids
[{'default': True, 'id': '7479735', 'url': 'example.com'},
 {'default': False, 'id': '7746580', 'url': 'm.example.com'}]
>>> l.site_id = '7746580'
```

### Get Preview ###

`l.get_perview()` return the first page of Baidu Tongji data.

The format looks like:

```
{'everyday_avg': {'avg_visit_time': 593,
                  'bounce_ratio': 20.05,
                  'ip_count': 1063,
                  'pv_count': 54928,
                  'trans_count': None,
                  'visitor_count': 2191},
 'forecase_today': {'avg_visit_time': {'flag': 0, 'val': None},
                    'bounce_ratio': {'flag': 0, 'val': None},
                    'ip_count': {'flag': -1, 'val': 446},
                    'pv_count': {'flag': -1, 'val': 15889},
                    'trans_count': {'flag': 0, 'val': None},
                    'visitor_count': {'flag': -1, 'val': 783}},
 'today': {'avg_visit_time': 497,
           'bounce_ratio': 20.66,
           'ip_count': 442,
           'pv_count': 15671,
           'trans_count': None,
           'visitor_count': 741},
 'yesterday': {'avg_visit_time': 450,
               'bounce_ratio': 20.33,
               'ip_count': 750,
               'pv_count': 35577,
               'trans_count': None,
               'visitor_count': 1727},
 'yesterday_now': {'avg_visit_time': 467,
                   'bounce_ratio': 20.56,
                   'ip_count': 730,
                   'pv_count': 34849,
                   'trans_count': None,
                   'visitor_count': 1616}},
 'history_peak': {'avg_visit_time': {'date': datetime.datetime(2015, 12, 28, 0, 0),
    'show': 0,
    'val': 907},
   'bounce_ratio': {'date': datetime.datetime(2015, 12, 22, 0, 0),
    'show': 0,
    'val': 28.07},
   'ip_count': {'date': datetime.datetime(2015, 12, 29, 0, 0),
    'show': 1,
    'val': 736},
   'pv_count': {'date': datetime.datetime(2015, 12, 29, 0, 0),
    'show': 1,
    'val': 29717},
   'trans_count': None,
   'visitor_count': {'date': datetime.datetime(2015, 12, 29, 0, 0),
    'show': 1,
    'val': 994}}
```

### Get Location ###

`get_region(date)` get one day information of all provinces.
`date` can be `datetime.date` object
(which , must has `year`, `month`, `day` attribute)

```python
import datetime
datetime.date(year=2015, month=12, day=2)
result = l.get_region(d)
print(result)
```

`has_city_regions()` return all provinces which contains sub-cities.

`get_city(region, date)` return the information of cities under `region` province
at `date` date.

```python
for each in l.has_city_regions():
    this_result = l.get_city(each, d)
    print(this_result)
```

### Logout ###

`.logout()` will delete all cookie to start a new session.

Error
-----

raise `baidutongji.NotLoginError` when you try to get data with a outdated
session or not logged in.