from flask import Flask, render_template, request, redirect, send_file
import pandas as pd
import io
import os
import numpy as np

app = Flask(__name__)

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
    heatmap_labels = []
    heatmap_values = []
    insights = None

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

        # ===== ADVANCED SORTING =====
        if "sort" in request.form and df is not None:

            sort_type = request.form.get("sort_type")
            order = request.form.get("sort_order")

            numeric_df = df.select_dtypes(include=[np.number])

            if sort_type == "column":
                column = request.form.get("sort_column")
                if column in df.columns:
                    df[column] = pd.to_numeric(df[column], errors="coerce")
                    df = df.sort_values(by=column, ascending=(order == "asc"))

            elif sort_type == "row_avg" and not numeric_df.empty:
                df["__row_avg__"] = numeric_df.mean(axis=1)
                df = df.sort_values(by="__row_avg__", ascending=(order == "asc"))
                df.drop(columns=["__row_avg__"], inplace=True)

            elif sort_type == "row_max" and not numeric_df.empty:
                df["__row_max__"] = numeric_df.max(axis=1)
                df = df.sort_values(by="__row_max__", ascending=(order == "asc"))
                df.drop(columns=["__row_max__"], inplace=True)

        # Heatmap
        if "heatmap" in request.form and df is not None:
            numeric_df = df.select_dtypes(include=[np.number])
            if not numeric_df.empty:
                corr_matrix = numeric_df.corr().round(2)
                heatmap_labels = corr_matrix.columns.tolist()
                heatmap_values = corr_matrix.values.tolist()

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

    # ===== DISPLAY DATA =====
    if df is not None:

        numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()
        table = df.to_html(classes="table", index=False)

        kpis = {
            "rows": df.shape[0],
            "columns": df.shape[1],
            "numeric_cols": len(numeric_columns),
            "missing": int(df.isnull().sum().sum())
        }

        # ===== INSIGHTS =====
        insights = {}

        missing_series = df.isnull().sum()
        max_missing_col = missing_series.idxmax()
        insights["most_missing"] = f"{max_missing_col} ({int(missing_series.max())})"

        numeric_df = df.select_dtypes(include=[np.number])

        if len(numeric_df.columns) > 1:
            corr_matrix = numeric_df.corr()
            corr_matrix.values[[np.arange(len(corr_matrix))]*2] = np.nan
            max_corr = corr_matrix.unstack().dropna().idxmax()
            min_corr = corr_matrix.unstack().dropna().idxmin()
            insights["strongest_positive"] = f"{max_corr[0]} & {max_corr[1]}"
            insights["strongest_negative"] = f"{min_corr[0]} & {min_corr[1]}"

        if len(numeric_df.columns) > 0:
            variance_series = numeric_df.var()
            insights["highest_variance"] = variance_series.idxmax()

    return render_template(
        "index.html",
        table=table,
        numeric_columns=numeric_columns,
        error_message=error_message,
        kpis=kpis,
        heatmap_labels=heatmap_labels,
        heatmap_values=heatmap_values,
        insights=insights
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
