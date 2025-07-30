# Marcus

## Setup Project

### _Requirements_

1. **Python 3.13** or above
1. [**NodeJs LTS**](https://nodejs.org/en/download)  This is built on version **22.16.0**
1. [**Docker Desktop**](https://www.docker.com/products/docker-desktop)
1. [**Playwright**](https://playwright.dev/docs/intro)
1. [**uv**](https://docs.astral.sh/uv/getting-started/installation/)  python package manager

### 1. Clone the Repository

```sh
git clone https://github.com/vrsarin/marcus.git
cd marcus
```

### 2. Create a Virtual Environment

```sh
uv venv
uv pip install . --group test --group poc  # you can drop poc if not required
```

OR

```sh
make setup
```

### 3. Activate the Virtual Environment

- **Windows:**

  ```sh
  # CMD
  .venv\Scripts\activate

  # Powershell
  .venv\Scripts\Activate.ps1
  ```

- **Linux/macOS:**

  ```sh
  source .venv/bin/activate
  ```
