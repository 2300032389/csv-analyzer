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

    df = None

    # =====================
    # CSV Upload
    # =====================
    if request.method == "POST":

        if "upload_csv" in request.form:
            file = request.files.get("csv_file")

            if file and file.filename != "":
                try:
                    df = pd.read_csv(file)
                except Exception as e:
                    return f"Error reading file: {str(e)}"

        # =====================
        # Analyze
        # =====================
        if "analyze" in request.form:
            file = request.files.get("csv_file")

            if file and file.filename != "":
                df = pd.read_csv(file)

            if df is not None:
                selected_columns = request.form.getlist("columns")
                chart_type = request.form.get("chart_type", "bar")

                if selected_columns:
                    numeric_data = df[selected_columns].apply(pd.to_numeric, errors="coerce")

                    stats = {}
                    for col in selected_columns:
                        column_data = numeric_data[col].dropna()
                        stats[col] = {
                            "average": round(column_data.mean(), 2),
                            "highest": column_data.max(),
                            "lowest": column_data.min()
                        }

                    labels = df.index.astype(str).tolist()
                    values = numeric_data.fillna(0).values.tolist()

        # =====================
        # Download
        # =====================
        if "download" in request.form:
            file = request.files.get("csv_file")

            if file and file.filename != "":
                df = pd.read_csv(file)

                buffer = io.StringIO()
                df.to_csv(buffer, index=False)
                buffer.seek(0)

                return send_file(
                    io.BytesIO(buffer.getvalue().encode()),
                    mimetype="text/csv",
                    as_attachment=True,
                    download_name="processed_data.csv"
                )

    # Detect numeric columns only if df exists
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
        values=values
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
