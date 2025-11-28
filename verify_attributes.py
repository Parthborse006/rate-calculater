import flet as ft

def check_attr(obj, attr_name):
    try:
        val = getattr(obj, attr_name)
        print(f"OK: {obj.__name__}.{attr_name}")
    except AttributeError:
        print(f"ERROR: {obj.__name__} has no attribute '{attr_name}'")

print("Checking Flet attributes...")
check_attr(ft, "ThemeMode")
check_attr(ft, "Icons")
check_attr(ft, "KeyboardType")
check_attr(ft, "FontWeight")
check_attr(ft, "TextAlign")
check_attr(ft, "BoxShadow")
check_attr(ft, "alignment")
check_attr(ft, "DatePicker")
check_attr(ft, "ElevatedButton")
check_attr(ft, "TextField")
check_attr(ft, "Container")
check_attr(ft, "Column")
check_attr(ft, "Text")

try:
    print(f"OK: ft.Icons.CALENDAR_TODAY = {ft.Icons.CALENDAR_TODAY}")
except AttributeError:
    print("ERROR: ft.Icons.CALENDAR_TODAY missing")

try:
    print(f"OK: ft.ThemeMode.LIGHT = {ft.ThemeMode.LIGHT}")
except AttributeError:
    print("ERROR: ft.ThemeMode.LIGHT missing")
