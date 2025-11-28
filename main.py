import flet as ft
from datetime import datetime

def main(page: ft.Page):
    page.title = "Interest Calculator"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.window_width = 400
    page.window_height = 700
    
    # Custom Colors
    primary_color = "#6200EE"
    background_color = "#F5F5F5"
    card_color = "#FFFFFF"

    page.bgcolor = background_color

    def calculate_click(e):
        try:
            if not principal_field.value:
                result_text.value = "Please enter principal amount"
                result_text.color = ft.Colors.RED
                page.update()
                return
            
            if not date_picker.value:
                 # If no date picked, try to parse text field if we had one, 
                 # but here we rely on the picker or default to today if logic allowed, 
                 # but let's force a pick or manual entry if we added it.
                 # For this UI, let's assume date_picker.value is populated after selection.
                 # If None, it means user hasn't picked one.
                 result_text.value = "Please select a start date"
                 result_text.color = ft.Colors.RED
                 page.update()
                 return

            principal = float(principal_field.value)
            start_date = date_picker.value
            current_date = datetime.now()
            
            days_diff = (current_date - start_date).days
            
            # Logic from days_cal.py:
            # interest_rate = 1.5 / 100  # 1.5%
            # for_preday = principal * interest_rate / 30
            # final_amount = principal + (for_preday * days_diff)
            
            interest_rate = 1.5 / 100
            daily_interest = (principal * interest_rate) / 30
            total_interest = daily_interest * days_diff
            final_amount = principal + total_interest
            
            result_text.value = (
                f"Days: {days_diff}\n"
                f"Interest: ₹{total_interest:.2f}\n"
                f"Total: ₹{final_amount:.2f}"
            )
            result_text.color = ft.Colors.BLACK
            
            # Animate result container
            result_container.opacity = 1
            result_container.update()
            
        except ValueError:
            result_text.value = "Invalid input"
            result_text.color = ft.Colors.RED
        
        page.update()

    # Date Picker
    date_picker = ft.DatePicker(
        on_change=lambda e: setattr(date_button, "text", e.control.value.strftime('%Y-%m-%d')) or date_button.update(),
    )
    # page.overlay.append(date_picker) # Not needed with page.open()
    
    date_button = ft.ElevatedButton(
        "Select Start Date",
        icon=ft.Icons.CALENDAR_TODAY,
        on_click=lambda _: page.open(date_picker),
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=primary_color,
            shape=ft.RoundedRectangleBorder(radius=10),
        ),
        height=50,
    )

    principal_field = ft.TextField(
        label="Principal Amount",
        prefix_text="₹ ",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_radius=10,
        filled=True,
        bgcolor=card_color,
    )

    calculate_btn = ft.ElevatedButton(
        text="Calculate",
        on_click=calculate_click,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=primary_color,
            shape=ft.RoundedRectangleBorder(radius=10),
        ),
        height=50,
        width=200,
    )

    result_text = ft.Text(
        size=18,
        weight=ft.FontWeight.BOLD,
        text_align=ft.TextAlign.CENTER,
    )
    
    result_container = ft.Container(
        content=result_text,
        padding=20,
        bgcolor=card_color,
        border_radius=15,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=10,
            color=ft.Colors.BLUE_GREY_100,
        ),
        opacity=0, # Hidden initially
        animate_opacity=300,
        alignment=ft.alignment.center
    )

    # Layout
    page.add(
        ft.Column(
            [
                ft.Container(height=20),
                ft.Text("Interest Calculator", size=30, weight=ft.FontWeight.BOLD, color=primary_color),
                ft.Container(height=20),
                principal_field,
                ft.Container(height=10),
                date_button,
                ft.Container(height=30),
                calculate_btn,
                ft.Container(height=30),
                result_container,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )

if __name__ == "__main__":
    ft.app(target=main)
