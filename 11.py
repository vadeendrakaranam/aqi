from flask import Flask, render_template, request
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

# --- Email Configuration ---
SENDER_EMAIL = "karanam.vadeendra123456@gmail.com"
SENDER_PASSWORD = "xrpc cyhe hwdn fxzp"  # Use app password for Gmail
RECEIVER_EMAIL = "126158026@sastra.ac.in"

def send_email(subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print("Email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {e}")

# --- AQI Logic ---
def calculate_cpcb_aqi(concentration, breakpoints):
    for (bp_lo, bp_hi, i_lo, i_hi) in breakpoints:
        if bp_lo <= concentration <= bp_hi:
            return round(((i_hi - i_lo) / (bp_hi - bp_lo)) * (concentration - bp_lo) + i_lo)
    return None

def classify_aqi_cpcb(aqi):
    if aqi <= 50:
        return 'Good'
    elif aqi <= 100:
        return 'Satisfactory'
    elif aqi <= 200:
        return 'Moderate'
    elif aqi <= 300:
        return 'Poor'
    elif aqi <= 400:
        return 'Very Poor'
    else:
        return 'Severe'

def get_cpcb_aqi(pm25=None, pm10=None, no2=None, co=None, o3=None):
    aqi_results = {}

    # CPCB breakpoints
    pm25_bp = [(0, 30, 0, 50), (31, 60, 51, 100), (61, 90, 101, 200),
               (91, 120, 201, 300), (121, 250, 301, 400), (251, 500, 401, 500)]
    pm10_bp = [(0, 50, 0, 50), (51, 100, 51, 100), (101, 250, 101, 200),
               (251, 350, 201, 300), (351, 430, 301, 400), (431, 1000, 401, 500)]
    no2_bp = [(0, 40, 0, 50), (41, 80, 51, 100), (81, 180, 101, 200),
              (181, 280, 201, 300), (281, 400, 301, 400), (401, 1000, 401, 500)]
    co_bp = [(0, 1, 0, 50), (1.1, 2, 51, 100), (2.1, 10, 101, 200),
             (10.1, 17, 201, 300), (17.1, 34, 301, 400), (34.1, 50, 401, 500)]
    o3_bp = [(0, 50, 0, 50), (51, 100, 51, 100), (101, 168, 101, 200),
             (169, 208, 201, 300), (209, 748, 301, 400), (749, 1000, 401, 500)]

    if pm25 is not None:
        aqi_results['PM2.5'] = calculate_cpcb_aqi(pm25, pm25_bp)
    if pm10 is not None:
        aqi_results['PM10'] = calculate_cpcb_aqi(pm10, pm10_bp)
    if no2 is not None:
        aqi_results['NO2'] = calculate_cpcb_aqi(no2, no2_bp)
    if co is not None:
        aqi_results['CO'] = calculate_cpcb_aqi(co, co_bp)
    if o3 is not None:
        aqi_results['O3'] = calculate_cpcb_aqi(o3, o3_bp)

    if not aqi_results:
        return None, None, None, {}

    max_pollutant = max(aqi_results, key=aqi_results.get)
    max_aqi = aqi_results[max_pollutant]
    category = classify_aqi_cpcb(max_aqi)

    return max_aqi, max_pollutant, category, aqi_results


@app.route("/", methods=["GET", "POST"])
def index():
    aqi_data = {}
    if request.method == "POST":
        df = pd.read_csv("livedata.csv")

        if len(df) < 24:
            aqi_data["error"] = "Not enough data to calculate AQI. Need at least 24 rows."
        else:
            latest_24 = df.tail(24)
            pm25 = latest_24["PM2.5"].mean()
            pm10 = latest_24["PM10"].mean()
            no2 = latest_24["NO2"].mean()
            co = latest_24["CO"].mean()
            o3 = latest_24["O3"].mean()

            overall_aqi, main_pollutant, category, all_aqis = get_cpcb_aqi(pm25, pm10, no2, co, o3)

            aqi_data = {
                "overall_aqi": overall_aqi,
                "category": category,
                "main_pollutant": main_pollutant,
                "all_aqis": all_aqis
            }

            # --- Send Email Notification ---
            subject = f"AQI Report: {category} ({overall_aqi})"
            body = (
                f"AQI Report:\n\n"
                f"Overall AQI: {overall_aqi}\n"
                f"Main Pollutant: {main_pollutant}\n"
                f"Category: {category}\n\n"
                f"Individual AQIs:\n" +
                "\n".join([f"{k}: {v}" for k, v in all_aqis.items()])
            )
            send_email(subject, body)

    return render_template("index.html", data=aqi_data)


if __name__ == "__main__":
    app.run(debug=True)
