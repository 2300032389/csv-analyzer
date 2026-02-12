from flask import Flask, render_template, request, redirect, send_file
import pandas as pd
import io
import os

app = Flask(__name__)

# Simple in-memory storage (single-user demo mode)
df = None


@app.route("/", methods=["GET", "POST"])
def index():
    global df

    error_message = None
    stats = None
    table = None
    numeric_columns = []
    labels = []
    values = []
    chart_type = "bar"
    kpis = None

    if request.method == "POST":

        # Upload CSV
        if "upload_csv" in request.form:
            file = request.files.get("csv_file")

            if not file or file.filename == "":
                error_message = "Please upload a CSV file."
            else:
                try:
                    df = pd.read_csv(file)

                    if df.empty:
                        error_message = "Uploaded CSV is empty."
                        df = None

                except Exception as e:
                    error_message = f"Invalid CSV file: {str(e)}"
                    df = None

        # Reset
        if "reset" in request.form:
            df = None
            return redirect("/")

        # Sort
        if "sort" in request.form and df is not None:
            column = request.form.get("sort_column")
            order = request.form.get("sort_order")

            if column in df.columns:
                df[column] = pd.to_numeric(df[column], errors="coerce")
                df = df.sort_values(by=column, ascending=(order == "asc"))

        # Analyze
        if "analyze" in request.form and df is not None:
            selected_columns = request.form.getlist("columns")
            chart_type = request.form.get("chart_type", "bar")

            if selected_columns:
                numeric_data = df[selected_columns].apply(
                    pd.to_numeric, errors="coerce"
                )

                stats = {}
                for col in selected_columns:
                    column_data = numeric_data[col].dropna()
                    if not column_data.empty:
                        stats[col] = {
                            "average": round(column_data.mean(), 2),
                            "highest": column_data.max(),
                            "lowest": column_data.min()
                        }

                labels = df.index.astype(str).tolist()
                values = numeric_data.fillna(0).values.tolist()

        # Download
        if "download" in request.form and df is not None:
            buffer = io.StringIO()
            df.to_csv(buffer, index=False)
            buffer.seek(0)

            return send_file(
                io.BytesIO(buffer.getvalue().encode()),
                mimetype="text/csv",
                as_attachment=True,
                download_name="processed_data.csv"
            )

    # Prepare display data
    if df is not None:
        numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()
        table = df.to_html(classes="table", index=False)

        kpis = {
            "rows": df.shape[0],
            "columns": df.shape[1],
            "numeric_cols": len(numeric_columns),
            "missing": int(df.isnull().sum().sum())
        }

    return render_template(
        "index.html",
        table=table,
        stats=stats,
        numeric_columns=numeric_columns,
        labels=labels,
        values=values,
        chart_type=chart_type,
        error_message=error_message,
        kpis=kpis
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
