from flask import Flask, render_template, request, send_file
import pandas as pd
import io
import os

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():

    table = None
    stats = None
    numeric_columns = []
    selected_columns = []
    chart_type = "bar"
    labels = []
    values = []
    error_message = None

    df = None

    if request.method == "POST":

        file = request.files.get("csv_file")

        if not file or file.filename == "":
            error_message = "Please upload a CSV file."
        else:
            try:
                df = pd.read_csv(file)

                if df.shape[1] == 0:
                    error_message = "CSV file contains no columns."
                    df = None

            except pd.errors.EmptyDataError:
                error_message = "Uploaded CSV is empty."
                df = None

            except Exception as e:
                error_message = f"Invalid CSV file: {str(e)}"
                df = None

        # =========================
        # SORTING
        # =========================
        if "sort" in request.form and df is not None:
            sort_column = request.form.get("sort_column")
            sort_order = request.form.get("sort_order")

            if sort_column in df.columns:
                df[sort_column] = pd.to_numeric(df[sort_column], errors="coerce")
                df = df.sort_values(
                    by=sort_column,
                    ascending=(sort_order == "asc")
                )

        # =========================
        # ANALYZE
        # =========================
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

        # =========================
        # DOWNLOAD
        # =========================
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

    if df is not None:
        numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()
        table = df.to_html(classes="table", index=False)

    return render_template(
        "index.html",
        table=table,
        stats=stats,
        numeric_columns=numeric_columns,
        selected_columns=selected_columns,
        chart_type=chart_type,
        labels=labels,
        values=values,
        error_message=error_message
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
