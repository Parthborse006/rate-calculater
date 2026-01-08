# Interest Calculator

<img src="assets/icon.png" width="100" height="100" alt="App Icon">

A simple and elegant Interest Calculator app built with [Flet](https://flet.dev) (Python). This app allows you to calculate interest based on a principal amount and a start date.

## Features

-   **Calculate Interest**: Calculates daily and total interest based on a 1.5% monthly rate.
-   **Date Picker**: Easy-to-use calendar for selecting the start date.
-   **Material Design**: Clean and modern UI using Flet's Material controls.
-   **Cross-Platform**: Runs on Windows, macOS, Linux, Web, and Android.
-   **Custom Icon**: Now features a modern, custom-designed app icon.

## Prerequisites

-   Python 3.11+
-   `pip` (Python package manager)

## Installation & Running Locally

1.  **Clone the repository**:
    ```bash
    git clone <your-repo-url>
    cd calculater
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the app**:
    ```bash
    flet run main.py
    ```
    *Note: You can also run it with `python main.py`*

## Building for Android

This project is set up with GitHub Actions to automatically build an Android APK.

1.  **Push changes to GitHub**:
    ```bash
    git push origin main
    ```

2.  **Download APK**:
    -   Go to the **Actions** tab in your GitHub repository.
    -   Click on the latest workflow run.
    -   Download the `app-release` artifact.

3.  **Install**:
    -   Transfer the APK to your Android device and install it.

## Technologies Used

-   [Flet](https://flet.dev) - Python framework for building Flutter apps.
-   Python - Core logic.
