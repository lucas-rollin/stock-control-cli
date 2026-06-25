import sqlite3
from datetime import datetime
from dataclasses import dataclass
from collections.abc import Callable
from rich import print
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.console import Group


DATABASE_PATH = "stock.db"

# Column configuration: (display_name, data_type)
HEADER_MAP = {
    "id": ("ID", "int"),
    "name": ("Nome", "str"),
    "active": ("Ativo", "bool"),
    "product_id": ("ID do Produto", "int"),
    "employee_id": ("ID do Funcionário", "int"),
    "quantity": ("Quantidade", "float"),
    "created_at": ("Criado em", "datetime")
}

# Data type formatter
TYPE_FORMATTERS = {
    "int": lambda x: str(x),
    "str": lambda x: str(x) if x else "",
    "bool": lambda x: "Sim" if x == 1 else "Não",
    "float": lambda x: f"{x:.2f}".replace('.', ',') if x is not None else "0,00",
    "datetime": lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M:%S").strftime('%d/%m/%Y %H:%M:%S') if x else ""
}


# ---------------------------------------------------
# Helper Functions 
# ---------------------------------------------------

def run_sql(query: str, params=(), fetch=False):
    """
    Helper function to run sqlite3 queries.

    Params:
        query: The SQL query string.
        params: The parameters that replace placeholders "?" in query.
        fetch: Whether this is a select query.

    Returns:
        A list of tuples with query result if fetch else None.
    """
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)

            if fetch:
                headers = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                return headers, rows

    except sqlite3.Error as e:
        raise RuntimeError(f"Database error occurred: {e}") from e


def display_values(
        query: str, 
        title: str = "Visualização de Dados",
        inner_text: str|None = None,
    ) -> list[str]:
    """
    Generic data visualization function.
    
    Args:
        query: The SQL select query.
        title: Text place at the top of the panel.
        inner_text: Text placed inside the panel above the table.

    Returns:
        The list of ids from the lookup.
    """
    if not query.strip().startswith("SELECT"):
        raise("Attempted non select query")

    headers, rows = run_sql(query, fetch=True)

    headers_display = [HEADER_MAP.get(h, h)[0] for h in headers]

    lookup_ids = [str(p[0]) for p in rows]

    # Build a table
    table = Table(show_header=True, header_style="bold magenta")
    for h in headers_display:
        table.add_column(h, style="cyan")

    # Convert row values to formatted strings before appending
    for row in rows:
        row_display = []
        for i, e in enumerate(row):
            _, data_type = HEADER_MAP[headers[i]]
            type_formater = TYPE_FORMATTERS[data_type]
            value = type_formater(e)
            row_display.append(value)
        table.add_row(*row_display)

    if inner_text:    
        panel_content = Group(
            inner_text,
            table
        )
    else:
        panel_content = table

    print(Panel.fit(panel_content, title=title))

    return lookup_ids

# -----------------------------------------------
# Visualization and Database Interaction
# -----------------------------------------------

def display_logging_values(
        title: str = "Visualização de Movimentação", 
        inner_text: str|None = None
    ):
    query = """
        SELECT 
            logging.id, 
            product.name AS "Nome Produto", 
            employee.name AS "Nome Funcionário", 
            quantity, 
            created_at
        FROM logging JOIN product ON product_id = product.id, 
        employee ON employee_id = employee.id
    """
    return display_values(query, title, inner_text)


def display_stock_values(
        title: str = "Visualização de Estoque", 
        inner_text: str|None = None
    ) :
    query = """
        SELECT stock.id, quantity, name
        FROM stock JOIN product ON product_id = product.id
        WHERE product.active = true
    """
    return display_values(query, title, inner_text)


def display_stock_change_view(entry=True):
    """Display a stock view for product entry or leave."""
    valid_ids = display_stock_values(
        title=f"{'Entrada' if entry else 'Saída'} de Produtos",
        inner_text="[bold]Selecione um produto[/bold]"
    )
    valid_ids = [str(i) for i in valid_ids]

    while True:
        product_id = Prompt.ask("Escolha um produto (digite o ID)")
        if product_id not in valid_ids:
            print("[red]Digite uma opção válida[/red]\n")
        else:
            print()
            break
    
    while True:
        employee_name = Prompt.ask("Qual o nome do funcionário?")
 
        employee_query = "SELECT id, name, active FROM employee WHERE name = ?"
        result = run_sql(employee_query, (employee_name,), True)[1]
        if not result:
            print("\n[red]Funcionário não encontrado[/red]\n")
        elif result[0][2] != 1:
            print("\n[red]Funcionário não está ativo[/red]\n")
        else:
            employee_id = result[0][0]
            print()
            break
            
    while True:
        quantity_str = Prompt.ask("Qual quantidade?")
        try:
            quantity_change = float(quantity_str)

            # Quantity must be positive as sign is defined by the route
            if quantity_change <= 0:
                print("[red]Digite um número positivo[/red]\n")
            else:
                quantity_query = "SELECT quantity FROM stock WHERE id = ?"
                available_quantity = run_sql(quantity_query, (product_id,), True)[1][0][0]
                
                # New quantity after the transaction must be positive
                if not entry:
                    new_quantity = available_quantity - quantity_change
                    if new_quantity < 0:
                        print("[red]Digite uma quantidade menor que o existente para saída[/red]\n")
                    else:
                        break
                else:
                    new_quantity = available_quantity + quantity_change
                    break
        except ValueError:
            print("[red]Digite um número[/red]\n")

    run_stock_change(product_id, employee_id, new_quantity, quantity_change) 
    print(
        f"[green]✓ {'Entrada' if entry else 'Saída'}" 
        " registrada com sucesso.[/green]\n"
    )


def run_stock_change(
        product_id: str, 
        employee_id: str,
        new_quantity: float, 
        quantity_change: float
    ):
    """Execute stock change in a transaction."""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE stock
                SET quantity = ?
                WHERE product_id = ?
            """, (new_quantity, product_id))

            cursor.execute("""
                INSERT INTO logging (product_id, employee_id, quantity)
                VALUES (?, ?, ?)
            """, (product_id, employee_id, quantity_change))

    except sqlite3.Error as e:
        raise RuntimeError(f"Database error occurred: {e}") from e


def display_soft_delete_view(table_name: str, display_name: str):
    """Generic data soft delete function."""
    valid_ids = display_values(
        query=f"SELECT * FROM {table_name}",
        inner_text=f"Selecione um {display_name}",
        title=f"Deleção de {display_name.capitalize()}"
    )

    while True:
        id = Prompt.ask(f"Escolha um {display_name} (digite o ID)")
        
        if id == "0":
            return
        
        elif id not in valid_ids:
            print("[red]Digite uma opção válida[/red]\n")
            
        else:

            run_sql(
                f"UPDATE {table_name} SET active = 0 WHERE id = ?",
                (id,)
            )
            
            print(f"[green]✓ {display_name.capitalize()} deletado com sucesso.[/green]\n")
            return


def display_create_view(table_name: str, display_name: str):
    """Generic data create function."""
    print(Panel.fit(
        f"Digite o nome do {display_name} ou [bold]0[/bold] para voltar.",
        title=f"Cadastro de {display_name.capitalize()}"
    ))

    while True:
        name = Prompt.ask(f"Nome do {display_name}").strip()

        if name == "0":
            return

        if not name:
            print(f"[red]O nome do {display_name} não pode ser vazio.[/red]\n")
            continue
        
        run_sql(
            f"INSERT INTO {table_name} (name) VALUES (?)",
            (name,)
        )

        print(f"[green]✓ {display_name.capitalize()} '{name}' cadastrado com sucesso.[/green]\n")



# -----------------------------------------------
# Menus, routes and main loop
# -----------------------------------------------

@dataclass
class Menu:
    title: str
    routes: dict[str, tuple[str, Callable]] # defines navigation and execution
    is_root: bool = False

    def display(self) -> None:
        """Displays a menu panel with navigation options."""
        while True:
            items = "\n".join(
                f"[cyan]{key}[/cyan]. {label}"
                for key, (label, _) in self.routes.items()
            ) 

            if self.is_root:
                items += "\n[cyan]0[/cyan]. Sair"
            else:
                items += "\n[cyan]0[/cyan]. Voltar"

            print(Panel.fit(
                f"[bold]O que deseja fazer?[/bold]\n{items}",
                title=self.title
            ))
        
            choice = Prompt.ask("Escolha uma opção")
            
            if choice == "0":
                print()
                return
            elif choice in self.routes:
                print()
                _, func = self.routes[choice]
                func()
            else:
                print("[red]Digite uma opção válida[/red]\n")


STOCK_MENU = Menu(
    title="Menu de Estoque",
    routes={
        "1": ("Visualizar", display_stock_values),
        "2": ("Entrada de Produto", lambda: display_stock_change_view(entry=True)),
        "3": ("Saída de Produto", lambda: display_stock_change_view(entry=False)),
    }
)

PRODUCT_MENU = Menu(
    title="Menu de Produtos",
    routes={
        "1": ("Visualizar", lambda: display_values("SELECT * FROM product", title="Visualização de Produtos")),
        "2": ("Criar", lambda: display_create_view("product", "produto")),
        "3": ("Deletar", lambda: display_soft_delete_view("product", "produto")),
    }
)

EMPLOYEE_MENU = Menu(
    title="Menu de Funcionários",
    routes={
        "1": ("Visualizar", lambda: display_values("SELECT * FROM employee", title="Visualização de Funcionários")),
        "2": ("Criar", lambda: display_create_view("employee", "funcionário")),
        "3": ("Deletar", lambda: display_soft_delete_view("employee", "funcionário")),
    }
)

LOGGING_MENU = Menu(
    title="Menu de Movimentações",
    routes={
        "1": ("Visualizar",  display_logging_values),
    }
)

MAIN_MENU = Menu(
    title="Menu Principal",
    routes={
        "1": ("Estoque", STOCK_MENU.display),
        "2": ("Produtos", PRODUCT_MENU.display),
        "3": ("Funcionários", EMPLOYEE_MENU.display),
        "4": ("Movimentações", LOGGING_MENU.display),
    },
    is_root=True
)


def main():
    MAIN_MENU.display()


if __name__ == "__main__":
    main()