# Stock Control CLI

A simple command-line interface for managing inventory, products, employees, and stock movements with a SQLite database.

## Features

- **Product Management**: Create, view, and soft-delete products
- **Employee Management**: Create, view, and soft-delete employees
- **Stock Management**: View current stock levels
- **Stock Movements**: Record product entries (add to stock) and exits (remove from stock)
- **Movement History**: View all stock movement logs
- **Data Validation**: Ensures data integrity with constraints and triggers
- **Rich CLI Interface**: Colorful and user-friendly terminal interface

## Installation

1. Clone or download the repository
2. Install the dependencies:

```bash
pip install -r requirements.txt
```

3. Initialize the database:

```bash
sqlite3 stock.db < schema.sql
```

## Usage

```bash
python main.py
```

