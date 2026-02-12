from flask import Flask, render_template, request, redirect, session, send_file
import pandas as pd
import io
import os
import uuid

app = Flask(__name__)
app.secret_key = "clean_final_version_key"

# In-memory storage per user
user_data = {}


def get_user_id():
    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())
    return session["user_id"]


@app.route("/", methods=["GET", "POST"])
def index():

    user_id = get_user_id()
    df = user_data.get(user_id)

    error_message = None
    stats = None
    table = None
    numeric_columns = []
    labels = []
    values = []
    chart_type = "bar"

    if request.method == "POST":

        # Upload
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
                        user_data[user_id] = df

                except Exception as e:
                    error_message = f"Invalid CSV: {str(e)}"
                    df = None

        # Reset
        if "reset" in request.form:
            user_data.pop(user_id, None)
            return redirect("/")

        # Sort
        if "sort" in request.form and df is not None:
            column = request.form.get("sort_column")
            order = request.form.get("sort_order")

            if column in df.columns:
                df[column] = pd.to_numeric(df[column], errors="coerce")
                df = df.sort_values(by=column, ascending=(order == "asc"))
                user_data[user_id] = df

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
