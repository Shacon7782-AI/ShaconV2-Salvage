import traceback
try:
    from pydantic.v1.fields import FieldInfo
except Exception as e:
    traceback.print_exc()
