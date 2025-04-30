import streamlit as st
import pandas as pd
import numpy as np
import time
import folium
from streamlit_folium import folium_static
from datetime import datetime, timedelta
import random

# Set up the page
st.set_page_config(page_title="Way4U Pro Tipper Monitoring", layout="wide")
st.title("🚛 Tipper Truck Monitoring System")
st.subheader("Way4U Pro Configuration Demo")

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    num_trucks = st.slider("Number of Tipper Trucks", 1, 10, 5)
    alert_threshold = st.number_input("Stoppage Alert Threshold (minutes)", 10)
    geofence_radius = st.number_input("Geofence Radius (meters)", 100)
    simulate_data = st.button("Simulate Live Data")
    
    st.markdown("---")
    st.markdown("### Way4U Pro Settings")
    enable_trip_count = st.checkbox("Enable Automatic Trip Counting", True)
    enable_breakdown_alerts = st.checkbox("Enable Breakdown Alerts", True)
    enable_maintenance = st.checkbox("Enable Maintenance Alerts", True)

# Generate sample truck data
def generate_truck_data(num_trucks):
    trucks = []
    for i in range(1, num_trucks + 1):
        status = random.choice(["En Route to Mine", "Loading at Plant", "Unloading at Mine", "Returning to Plant"])
        if status == "En Route to Mine":
            lat = random.uniform(12.85, 12.95)
            lng = random.uniform(77.55, 77.65)
        elif status == "Returning to Plant":
            lat = random.uniform(12.75, 12.85)
            lng = random.uniform(77.45, 77.55)
        elif status == "Loading at Plant":
            lat = 12.80  # Plant location
            lng = 77.50
        else:
            lat = 12.90  # Mine location
            lng = 77.60
            
        trucks.append({
            "Truck ID": f"TIP-{i:03d}",
            "Status": status,
            "Last Update": (datetime.now() - timedelta(minutes=random.randint(0, 30))).strftime("%H:%M:%S"),
            "Current Trip": random.randint(1, 8),
            "Total Trips Today": random.randint(3, 12),
            "Latitude": lat,
            "Longitude": lng,
            "Speed": random.randint(0, 60),
            "Engine Status": random.choice(["Normal", "Warning", "Critical"]),
            "Stoppage Duration (min)": random.randint(0, 45) if status not in ["Loading at Plant", "Unloading at Mine"] else 0
        })
    return pd.DataFrame(trucks)

# Main dashboard
col1, col2 = st.columns([3, 1])

with col1:
    st.header("Real-Time Monitoring Dashboard")
    
    # Generate and display truck data
    truck_data = generate_truck_data(num_trucks)
    
    # Create a map
    m = folium.Map(location=[12.85, 77.55], zoom_start=11)
    
    # Add plant and mine geofences
    folium.Circle(
        location=[12.80, 77.50],  # Plant
        radius=geofence_radius,
        color='green',
        fill=True,
        fill_color='green',
        popup='Plant Loading Area'
    ).add_to(m)
    
    folium.Circle(
        location=[12.90, 77.60],  # Mine
        radius=geofence_radius,
        color='red',
        fill=True,
        fill_color='red',
        popup='Mine Unloading Area'
    ).add_to(m)
    
    # Add truck markers
    for idx, row in truck_data.iterrows():
        color = 'blue'
        if row['Engine Status'] == 'Warning':
            color = 'orange'
        elif row['Engine Status'] == 'Critical':
            color = 'red'
            
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=f"Truck {row['Truck ID']} - {row['Status']}",
            icon=folium.Icon(color=color, icon='truck', prefix='fa')
        ).add_to(m)
    
    folium_static(m, width=800, height=400)
    
    # Display truck data table
    st.dataframe(truck_data.style.apply(lambda x: ['background: #ffcccc' if x['Engine Status'] == 'Critical' else 
                                                 ('background: #ffe6cc' if x['Engine Status'] == 'Warning' else '') 
                                                 for i in x], axis=1))

with col2:
    st.header("Alerts & Notifications")
    
    # Breakdown alerts
    if enable_breakdown_alerts:
        breakdowns = truck_data[(truck_data['Stoppage Duration (min)'] > alert_threshold) & 
                              (~truck_data['Status'].isin(['Loading at Plant', 'Unloading at Mine']))]
        
        if not breakdowns.empty:
            st.error("🚨 Breakdown Alerts")
            for idx, row in breakdowns.iterrows():
                st.error(f"Truck {row['Truck ID']} stopped for {row['Stoppage Duration (min)']} minutes at {row['Status']}")
        else:
            st.success("No breakdown alerts")
    
    # Maintenance alerts
    if enable_maintenance:
        st.markdown("---")
        st.subheader("Maintenance Alerts")
        for idx, row in truck_data.iterrows():
            if row['Total Trips Today'] > 8:
                st.warning(f"Truck {row['Truck ID']} has completed {row['Total Trips Today']} trips today - consider maintenance soon")
    
    # Trip counting summary
    if enable_trip_count:
        st.markdown("---")
        st.subheader("Trip Counting")
        st.write(f"Average trips per truck: {truck_data['Total Trips Today'].mean():.1f}")
        st.bar_chart(truck_data.set_index('Truck ID')['Total Trips Today'])

# Simulation controls
if simulate_data:
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i in range(100):
        # Update the progress bar
        progress_bar.progress(i + 1)
        
        # Generate new data
        new_data = generate_truck_data(num_trucks)
        
        # Update the data display
        with col1:
            st.dataframe(new_data.style.apply(lambda x: ['background: #ffcccc' if x['Engine Status'] == 'Critical' else 
                                                       ('background: #ffe6cc' if x['Engine Status'] == 'Warning' else '') 
                                                       for i in x], axis=1))
        
        # Update alerts
        with col2:
            if enable_breakdown_alerts:
                breakdowns = new_data[(new_data['Stoppage Duration (min)'] > alert_threshold) & 
                                    (~new_data['Status'].isin(['Loading at Plant', 'Unloading at Mine']))]
                
                if not breakdowns.empty:
                    for idx, row in breakdowns.iterrows():
                        st.error(f"Truck {row['Truck ID']} stopped for {row['Stoppage Duration (min)']} minutes at {row['Status']}")
        
        status_text.text(f"Simulating data... {i+1}/100")
        time.sleep(0.1)
    
    st.success("Simulation complete!")

# Configuration guide
st.markdown("---")
st.header("Way4U Pro Configuration Guide")
with st.expander("Step-by-Step Setup Instructions"):
    st.markdown("""
    ### 1. Geofence Setup for Trip Counting
    - Create geofences around plant (loading) and mine (unloading) areas
    - Set radius to {} meters
    - Enable automatic trip counting when vehicles enter/exit these zones
    
    ### 2. Breakdown Alert Configuration
    - Set stoppage alert threshold to {} minutes
    - Configure alerts for unexpected stops outside geofenced areas
    - Enable engine diagnostics if OBD-II is connected
    
    ### 3. Real-Time Monitoring
    - View live positions on the map
    - Monitor trip counts and durations
    - Track engine status indicators
    
    ### 4. Maintenance Scheduling
    - Set up alerts based on trip counts or engine hours
    - Monitor for abnormal fuel consumption patterns
    """.format(geofence_radius, alert_threshold))

# Add some Way4U Pro branding
st.markdown("---")
st.markdown("*This demo simulates the functionality of Way4U Pro for tipper truck monitoring*")
