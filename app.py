import streamlit as st
import pandas as pd
from datetime import date, datetime
from src.models import Trip
from src.manager import TripManager
import os
import shutil
from pathlib import Path
from collections import Counter
import random
import pydeck as pdk

# Page Configuration
st.set_page_config(
    page_title="TravelLog | Your Digital Passport",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Look
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        border-radius: 8px;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .trip-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid #1f77b4;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .country-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        margin-bottom: 10px;
    }
    .metric-nice {
        font-size: 32px;
        font-weight: bold;
        color: #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Manager
BASE_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trips_data")
manager = TripManager(BASE_DATA_DIR)

# Country Coordinates for Map
COUNTRY_COORDS = {
    "China": [35.8617, 104.1954],
    "United States of America": [37.0902, -95.7129],
    "Switzerland": [46.8182, 8.2275],
    "Hungary": [47.1625, 19.5033],
    "United Arab Emirates": [23.4241, 53.8478],
    "Iceland": [64.9631, -19.0208],
    "Austria": [47.5162, 14.5501],
    "Norway": [60.4720, 8.4689],
    "France": [46.2276, 2.2137],
    "Germany, Federal Republic Of": [51.1657, 10.4515],
    "Japan": [36.2048, 138.2529],
    "Indonesia": [-0.7893, 113.9213],
    "United Kingdom": [55.3781, -3.4360],
    "Australia": [-25.2744, 133.7751],
    "Italy": [41.8719, 12.5674],
    "Spain": [40.4637, -3.7492],
    "Canada": [56.1304, -106.3468],
}
# Fallback for unknown countries
DEFAULT_COORD = [0.0, 0.0]

# Sidebar Navigation
with st.sidebar:
    st.title("TravelLog")
    st.markdown("---")
    page = st.radio("Navigation", ["Travel History", "Analytics", "Add New Trip"])
    
    st.markdown("---")
    st.info("Manage your international travel history with ease.")

# Helper to calculate stats
def get_stats(trips):
    total_trips = len(trips)
    countries = set(t.country for t in trips)
    total_countries = len(countries)
    
    total_days = 0
    for t in trips:
        try:
            # Parse dates (handle YYYY-MM and YYYY-MM-DD)
            d1 = datetime.strptime(t.start_date, "%Y-%m-%d") if len(t.start_date) == 10 else datetime.strptime(t.start_date, "%Y-%m")
            d2 = datetime.strptime(t.end_date, "%Y-%m-%d") if len(t.end_date) == 10 else datetime.strptime(t.end_date, "%Y-%m")
            duration = (d2 - d1).days
            total_days += max(0, duration)
        except Exception as e:
            pass
        
    return total_trips, total_countries, total_days

# Session State for Editing
if "editing_trip" not in st.session_state:
    st.session_state.editing_trip = None

# --- Page: Travel History ---
if page == "Travel History" and st.session_state.editing_trip is None:
    st.title("🌎 Travel History")
    
    trips = manager.scan_trips()
    
    if not trips:
        st.info("No trips recorded yet. Go to 'Add New Trip' to start your journey!")
    else:
        # Stats Row
        t_count, c_count, d_count = get_stats(trips)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Trips", t_count)
        with col2:
            st.metric("Countries Visited", c_count)
        with col3:
            st.metric("Total Days Traveled", d_count)
            
        st.markdown("### Recent Adventures")
        
        # Display Trips
        for trip in trips:
            # Show YYYY-MM for the title (works for both YYYY-MM-DD and YYYY-MM strings)
            display_date = trip.start_date[:7]
            with st.expander(f"{display_date} | {trip.city}, {trip.country}", expanded=False):
                col_info, col_actions = st.columns([3, 1])
                
                with col_info:
                    st.write(f"**Dates:** {trip.start_date} to {trip.end_date}")
                    st.write(f"**Notes:** {trip.notes}")
                    if trip.tags:
                        st.markdown(f"**Tags:** " + "".join([f"`{t}` " for t in trip.tags]))
                    
                    if trip.attachments:
                        st.write("**Attachments:**")
                        for att in trip.attachments:
                            att_path = manager.get_attachment_path(trip, att)
                            if att_path.exists():
                                with open(att_path, "rb") as f:
                                    st.download_button(
                                        label=f"📄 {att}",
                                        data=f.read(),
                                        file_name=att,
                                        key=f"{trip.id}_{att}",
                                        use_container_width=True
                                    )
                
                with col_actions:
                    if st.button("Edit", key=f"edit_{trip.id}", use_container_width=True):
                        st.session_state.editing_trip = trip
                        st.rerun()
                    
                    if st.button("Delete", key=f"del_{trip.id}", use_container_width=True):
                        if manager.delete_trip(trip.id):
                            st.success("Trip deleted!")
                            st.rerun()
                        else:
                            st.error("Failed to delete trip.")

# --- Page: Analytics ---
elif page == "Analytics":
    st.title("📊 Travel Analytics")
    
    trips = manager.scan_trips()
    if not trips:
         st.info("No trips data available yet.")
    else:
        # 1. Global Footprint Map
        st.subheader("🌍 Global Footprint")
        
        # Aggregate data for map
        country_counts = Counter([t.country for t in trips])
        map_data = []
        
        for country, count in country_counts.items():
            coords = COUNTRY_COORDS.get(country, DEFAULT_COORD)
            if coords != DEFAULT_COORD:
                map_data.append({
                    "lat": coords[0],
                    "lon": coords[1],
                    "country": country,
                    "visits": count,
                    "label": str(count)
                })
        
        if map_data:
            df_map = pd.DataFrame(map_data)
            
            # Use Pydeck for labels on map
            st.pydeck_chart(pdk.Deck(
                map_style='light',
                initial_view_state=pdk.ViewState(
                    latitude=20,
                    longitude=20,
                    zoom=1,
                    pitch=0,
                ),
                layers=[
                    pdk.Layer(
                        'ScatterplotLayer',
                        data=df_map,
                        get_position='[lon, lat]',
                        get_color='[31, 119, 180, 160]',
                        get_radius=200000,
                        pickable=True,
                    ),
                    pdk.Layer(
                        "TextLayer",
                        df_map,
                        get_position="[lon, lat]",
                        get_text="label",
                        get_size=20,
                        get_color=[255, 255, 255, 255],
                        get_alignment_baseline="'center'",
                    ),
                ],
                tooltip={"text": "{country}: {visits} visits"}
            ))
        else:
            st.warning("No map data available.")

        st.markdown("---")

        # 2. Top 3 Visited Countries
        st.subheader("🏆 Top 3 Destinations")
        
        top_3 = country_counts.most_common(3)
        
        cols = st.columns(3)
        
        for idx, (country, count) in enumerate(top_3):
            with cols[idx]:
                st.markdown(f"""
                <div class="country-card">
                    <div style="font-size: 40px;">🥇</div>
                    <h3>{country}</h3>
                    <div class="metric-nice">{count} Visits</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Find an image for this country
                country_image = None
                
                # Look for ANY trip to this country with an image
                relevant_trips = [t for t in trips if t.country == country]
                for t in relevant_trips:
                    if t.attachments:
                        # Check extensions
                        images = [att for att in t.attachments if att.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
                        if images:
                            # Pick random valid image
                            img_name = random.choice(images)
                            country_image = manager.get_attachment_path(t, img_name)
                            break # Found one
                
                if country_image and country_image.exists():
                    st.image(str(country_image), use_container_width=True)
                else:
                    # Placeholder if no image found
                    st.info("No photos uploaded yet.")

# --- Page: Add/Edit Trip ---
elif page == "Add New Trip" or st.session_state.editing_trip is not None:
    is_edit = st.session_state.editing_trip is not None
    current_trip = st.session_state.editing_trip
    
    title = "✏️ Edit Journey" if is_edit else "✈️ Record a New Journey"
    st.title(title)
    
    if is_edit:
        if st.button("← Back to Passport"):
            st.session_state.editing_trip = None
            st.rerun()

    with st.form("trip_form", clear_on_submit=not is_edit):
        col1, col2 = st.columns(2)
        
        with col1:
            city = st.text_input("City", value=current_trip.city if is_edit else "", placeholder="e.g. Paris")
            country = st.text_input("Country", value=current_trip.country if is_edit else "", placeholder="e.g. France")
            
        with col2:
            # Date Mode Selection
            # Check if current trip has specific days
            default_is_full = True
            if is_edit:
                default_is_full = (len(current_trip.start_date) == 10)
            
            date_mode = st.radio("Date Precision", ["Specific Days", "Month Only"], index=0 if default_is_full else 1, horizontal=True)
            
            if date_mode == "Specific Days":
                # Convert string dates back to date objects for the widget
                try:
                    def_start = date.fromisoformat(current_trip.start_date) if is_edit and len(current_trip.start_date) == 10 else date.today()
                    def_end = date.fromisoformat(current_trip.end_date) if is_edit and len(current_trip.end_date) == 10 else date.today()
                except:
                    def_start = def_end = date.today()

                date_range = st.date_input("Date Range", value=[def_start, def_end])
                
                if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
                    start_val, end_val = date_range[0].isoformat(), date_range[1].isoformat()
                elif isinstance(date_range, date):
                    start_val = end_val = date_range.isoformat()
                else:
                    start_val = end_val = date.today().isoformat()
            else:
                # Month-only mode implementation
                m_col1, m_col2 = st.columns(2)
                years = list(range(datetime.now().year + 2, 1990, -1))
                months = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
                
                # Default values for month mode
                def_s_y, def_s_m = datetime.now().year, f"{datetime.now().month:02d}"
                def_e_y, def_e_m = datetime.now().year, f"{datetime.now().month:02d}"
                
                if is_edit:
                    parts_s = current_trip.start_date.split("-")
                    def_s_y = int(parts_s[0])
                    def_s_m = parts_s[1]
                    parts_e = current_trip.end_date.split("-")
                    def_e_y = int(parts_e[0])
                    def_e_m = parts_e[1]

                with m_col1:
                    st.write("Start")
                    s_y = st.selectbox("Year", years, index=years.index(def_s_y), key="s_y")
                    s_m = st.selectbox("Month", months, index=months.index(def_s_m), key="s_m")
                    start_val = f"{s_y}-{s_m}"
                
                with m_col2:
                    st.write("End")
                    e_y = st.selectbox("Year", years, index=years.index(def_e_y), key="e_y")
                    e_m = st.selectbox("Month", months, index=months.index(def_e_m), key="e_m")
                    end_val = f"{e_y}-{e_m}"
        
        tags_value = ", ".join(current_trip.tags) if is_edit else ""
        tags_input = st.text_input("Tags (comma separated)", value=tags_value, placeholder="business, family, solo")
        
        notes_value = current_trip.notes if is_edit else ""
        notes = st.text_area("Notes", value=notes_value, placeholder="Describe your experience...")
        
        if is_edit and current_trip.attachments:
            st.info(f"Existing attachments: {', '.join(current_trip.attachments)}")
            
        uploaded_files = st.file_uploader("Upload more attachments", accept_multiple_files=True)
        
        button_label = "Update Trip" if is_edit else "Save Trip to TravelLog"
        submitted = st.form_submit_button(button_label)
        
        if submitted:
            if not city or not country:
                st.error("City and Country are required!")
            else:
                tags = [t.strip() for t in tags_input.split(",") if t.strip()]
                
                if is_edit:
                    updated_trip = Trip(
                        id=current_trip.id,
                        start_date=start_val,
                        end_date=end_val,
                        city=city,
                        country=country,
                        notes=notes,
                        tags=tags,
                        attachments=current_trip.attachments
                    )
                    
                    success = manager.save_trip(updated_trip, uploaded_files)
                    
                    if success:
                        st.success("Trip updated successfully!")
                        st.session_state.editing_trip = None
                        st.rerun()
                else:
                    new_trip = Trip(
                        start_date=start_val,
                        end_date=end_val,
                        city=city,
                        country=country,
                        notes=notes,
                        tags=tags
                    )
                    
                    success = manager.save_trip(new_trip, uploaded_files)
                    if success:
                        st.success(f"Trip to {city} saved successfully!")
                        st.balloons()
                    else:
                        st.error("Something went wrong while saving the trip.")
