METRICS = {
    "num_customers": lambda df: df["CustomerID"].nunique(),
    "total_quantity": lambda df: df["Quantity"].sum(),
    "total_revenue": lambda df: (df["Quantity"] * df["UnitPrice"]).sum(),
    "num_invoices": lambda df: df["InvoiceNo"].nunique(),
}
