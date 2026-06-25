CREATE TABLE IF NOT EXISTS product (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS employee (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS stock (
    id INTEGER PRIMARY KEY,
    product_id INTEGER UNIQUE NOT NULL,
    quantity REAL NOT NULL DEFAULT 0,

    FOREIGN KEY (product_id) REFERENCES product(id),
    CONSTRAINT quantity_must_be_positive CHECK(quantity >= 0)
);

CREATE TABLE IF NOT EXISTS logging (
    id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,
    quantity REAL NOT NULL, -- + entry / - removal
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (product_id) REFERENCES product(id),
    FOREIGN KEY (employee_id) REFERENCES employee(id)
);

CREATE TRIGGER create_stock_after_product
AFTER INSERT ON product
BEGIN
    INSERT INTO stock (product_id, quantity)
    VALUES (NEW.id, 0);
END;
