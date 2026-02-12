from flask import Flask, render_template, request, redirect, session, send_file
import pandas as pd
import io
import os
import base64

app = Flask(__name__)
app.secret_key = "placement_project_secret_key"


def load_dataframe():
    if "csv_data" in session:
        try:
            decoded = base64.b64decode(session["csv_data"])
            return pd.read_csv(io.BytesIO(decoded))
        except:
            return None
    return None


def save_dataframe(df):
    buffer = io.BytesIO()
    df.to_csv(buffer, index=False)
    session["csv_data"] = base64.b64encode(buffer.getvalue()).decode()


@app.route("/", methods=["GET", "POST"])
def index():

    error_message = None
    stats = None
    table = None
    numeric_columns = []
    labels = []
    values = []
    chart_type = "bar"

    df = load_dataframe()

    # =========================
    # HANDLE POST ACTIONS
    # =========================
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
                    else:
                        save_dataframe(df)

                except Exception as e:
                    error_message = f"Invalid CSV file: {str(e)}"
                    df = None

        # Reset Data
        if "reset" in request.form:
            session.pop("csv_data", None)
            return redirect("/")

        # Sort
        if "sort" in request.form and df is not None:
            column = request.form.get("sort_column")
            order = request.form.get("sort_order")

            if column in df.columns:
                df[column] = pd.to_numeric(df[column], errors="coerce")
                df = df.sort_values(by=column, ascending=(order == "asc"))
                save_dataframe(df)

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

    # Prepare data for display
    if df is not None:
        numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()
        table = df.to_html(classes="table", index=False)

    return render_template(
        "index.html",
        table=table,
        stats=stats,
        numeric_columns=numeric_columns,
        labels=labels,
        values=values,
        chart_type=chart_type,
        error_message=error_message
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
