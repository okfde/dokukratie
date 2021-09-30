# import re
# from datetime import date, datetime

# from dateparser import parse as dateparse2  # FIXME
# from dateutil.parser import ParserError
# from dateutil.parser import parse as dateparse
# from servicelayer import env

# from .exceptions import RegexError


# # def re_group(pattern, string, group):
# #     try:
# #         m = re.match(pattern, string)
# #         return m.group(group)
# #     except Exception:
# #         try:
# #             return re_first(pattern, string)
# #         except Exception as e:
# #             raise RegexError(str(e), string)


# # def flatten_dict(d):
# #     def items():
# #         for key, value in d.items():
# #             if isinstance(value, dict):
# #                 for subkey, subvalue in flatten_dict(value).items():
# #                     yield key + "." + subkey, subvalue
# #             else:
# #                 yield key, value

# #     return dict(items())
