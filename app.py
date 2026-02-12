from flask import Flask, render_template, request, send_file
import pandas as pd
import io

app = Flask(__name__)

uploaded_data = None

@app.route("/", methods=["GET", "POST"])
def index():
    global uploaded_data

    stats = None
    table = None
    numeric_columns = []
    selected_columns = []
    chart_type = "bar"
    labels = []
    values = []

    # =====================
    # Upload CSV
    # =====================
    if request.method == "POST":

        if "upload_csv" in request.form:
            file = request.files["csv_file"]

            if file.filename != "":
                try:
                    uploaded_data = pd.read_csv(file)
                except Exception as e:
                    return f"Error reading file: {str(e)}"

        # =====================
        # Analyze
        # =====================
        if "analyze" in request.form and uploaded_data is not None:

            selected_columns = request.form.getlist("columns")
            chart_type = request.form.get("chart_type")

            if selected_columns:

                numeric_data = uploaded_data[selected_columns].apply(pd.to_numeric, errors="coerce")

                stats = {}
                for col in selected_columns:
                    column_data = numeric_data[col].dropna()
                    stats[col] = {
                        "average": round(column_data.mean(), 2),
                        "highest": column_data.max(),
                        "lowest": column_data.min()
                    }

                labels = uploaded_data.index.astype(str).tolist()
                values = numeric_data[selected_columns].fillna(0).values.tolist()

        # =====================
        # Sort
        # =====================
        if "sort" in request.form and uploaded_data is not None:
            col = request.form["sort_column"]
            order = request.form["order"]

            uploaded_data[col] = pd.to_numeric(uploaded_data[col], errors="coerce")

            uploaded_data = uploaded_data.sort_values(
                by=col,
                ascending=(order == "asc")
            )

        # =====================
        # Download CSV
        # =====================
        if "download" in request.form and uploaded_data is not None:
            buffer = io.StringIO()
            uploaded_data.to_csv(buffer, index=False)
            buffer.seek(0)
            return send_file(
                io.BytesIO(buffer.getvalue().encode()),
                mimetype="text/csv",
                as_attachment=True,
                download_name="processed_data.csv"
            )

    if uploaded_data is not None:
        table = uploaded_data.to_html(classes="table", index=False)
        numeric_columns = uploaded_data.select_dtypes(include=["number"]).columns.tolist()

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
    app.run(debug=True)
