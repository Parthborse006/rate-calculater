import flet as ft
try:
    print(f"Red color: {ft.Colors.RED}")
    print("Success: ft.Colors.RED exists")
except AttributeError as e:
    print(f"Error: {e}")
