from flask import Flask, render_template, request, redirect, send_file
import pandas as pd
import numpy as np
import io
import os

app = Flask(__name__)

UPLOAD_PATH = "uploaded.csv"


def load_df():
    if os.path.exists(UPLOAD_PATH):
        try:
            return pd.read_csv(UPLOAD_PATH)
        except:
            return None
    return None


def save_df(df):
    df.to_csv(UPLOAD_PATH, index=False)


@app.route("/", methods=["GET", "POST"])
def index():

    error_message = None
    table = None
    numeric_columns = []
    kpis = None
    heatmap_labels = []
    heatmap_values = []

    insights = {
        "most_missing": "Not available",
        "strongest_positive": "Not available",
        "strongest_negative": "Not available",
        "highest_variance": "Not available"
    }

    df = load_df()

    if request.method == "POST":

        # Upload CSV
        if "upload_csv" in request.form:
            file = request.files.get("csv_file")

            if not file:
                error_message = "Please upload a CSV file."
            else:
                try:
                    df = pd.read_csv(file)

                    if df.empty:
                        error_message = "CSV is empty."
                        df = None
                    else:
                        save_df(df)

                except Exception as e:
                    error_message = f"Invalid CSV: {str(e)}"

        # Reset
        if "reset" in request.form:
            if os.path.exists(UPLOAD_PATH):
                os.remove(UPLOAD_PATH)
            return redirect("/")

        # Reload after possible upload
        df = load_df()

        # Sort
        if "sort" in request.form and df is not None:

            sort_type = request.form.get("sort_type")
            order = request.form.get("sort_order")
            numeric_df = df.select_dtypes(include=[np.number])

            if sort_type == "column":
                column = request.form.get("sort_column")
                if column in df.columns:
                    df = df.sort_values(by=column, ascending=(order == "asc"))

            elif sort_type == "row_avg" and not numeric_df.empty:
                df["__avg__"] = numeric_df.mean(axis=1)
                df = df.sort_values(by="__avg__", ascending=(order == "asc"))
                df.drop(columns=["__avg__"], inplace=True)

            elif sort_type == "row_max" and not numeric_df.empty:
                df["__max__"] = numeric_df.max(axis=1)
                df = df.sort_values(by="__max__", ascending=(order == "asc"))
                df.drop(columns=["__max__"], inplace=True)

            save_df(df)

        # Heatmap
        if "heatmap" in request.form and df is not None:
            numeric_df = df.select_dtypes(include=[np.number])
            if len(numeric_df.columns) > 1:
                corr = numeric_df.corr().round(2)
                heatmap_labels = corr.columns.tolist()
                heatmap_values = corr.values.tolist()

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
    df = load_df()

    if df is not None:

        numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()
        table = df.to_html(classes="table", index=False)

        kpis = {
            "rows": df.shape[0],
            "columns": df.shape[1],
            "numeric_cols": len(numeric_columns),
            "missing": int(df.isnull().sum().sum())
        }

        # Insights
        missing_series = df.isnull().sum()
        if not missing_series.empty:
            max_missing_col = missing_series.idxmax()
            max_missing_value = int(missing_series.max())
            insights["most_missing"] = f"{max_missing_col} ({max_missing_value})"

        numeric_df = df.select_dtypes(include=[np.number])

        if len(numeric_df.columns) > 1:
            corr_matrix = numeric_df.corr()
            np.fill_diagonal(corr_matrix.values, np.nan)
            stacked = corr_matrix.unstack().dropna()

            if not stacked.empty:
                max_corr = stacked.idxmax()
                min_corr = stacked.idxmin()

                insights["strongest_positive"] = f"{max_corr[0]} & {max_corr[1]}"
                insights["strongest_negative"] = f"{min_corr[0]} & {min_corr[1]}"

        if len(numeric_df.columns) > 0:
            variance_series = numeric_df.var()
            if not variance_series.empty:
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
    app.run(debug=True)
