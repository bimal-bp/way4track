import streamlit as st
from PIL import Image
import os
import pandas as pd
import psycopg2
from psycopg2 import sql
from datetime import datetime

# Database connection function
def get_db_connection():
    return psycopg2.connect(
        host="ep-bitter-snowflake-a4vh53sb-pooler.us-east-1.aws.neon.tech",
        database="neondb",
        user="neondb_owner",
        password="npg_AyD21VBQvTPW",
        sslmode="require"
    )

# Initialize database tables
def initialize_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create tires table if not exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tires (
        id SERIAL PRIMARY KEY,
        tipper_id VARCHAR(50) NOT NULL,
        tire_number VARCHAR(50) NOT NULL,
        position VARCHAR(50) NOT NULL,
        image_paths TEXT[],
        condition_percent INTEGER NOT NULL,
        date_installed DATE NOT NULL,
        starting_kmr INTEGER NOT NULL,
        current_kmr INTEGER NOT NULL,
        last_checked TIMESTAMP NOT NULL,
        UNIQUE(tipper_id, tire_number)
    )
    """)
    
    # Create tippers table if not exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tippers (
        tipper_id VARCHAR(50) PRIMARY KEY,
        registration VARCHAR(100) NOT NULL
    )
    """)
    
    # Insert tipper details if table is empty
    cursor.execute("SELECT COUNT(*) FROM tippers")
    if cursor.fetchone()[0] == 0:
        tipper_details = [
            ("TIPPER-101", "AP39UQ-0095"),
            ("TIPPER-403", "AP39WC-0928")
        ]
        
        for tipper in tipper_details:
            cursor.execute(
                "INSERT INTO tippers (tipper_id, registration) VALUES (%s, %s)",
                tipper
            )
    
    conn.commit()
    cursor.close()
    conn.close()

# Initialize database on app start
initialize_database()

# Function to get all tipper details
def get_tipper_details():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT tipper_id, registration FROM tippers")
    tippers = cursor.fetchall()
    cursor.close()
    conn.close()
    
    tipper_details = {}
    for tipper in tippers:
        display_name = f"{tipper[1]}"
        tipper_details[tipper[0]] = display_name
    return tipper_details

# Function to get all tires for a specific tipper
def get_tires_for_tipper(tipper_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT 
        tire_number, position, image_paths, 
        condition_percent, date_installed, starting_kmr, 
        current_kmr, last_checked
    FROM tires
    WHERE tipper_id = %s
    ORDER BY position
    """, (tipper_id,))
    tires = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return tires

# Function to save/update tire data
def save_tire_data(tipper_id, tire_number, position, image_path, condition, date_installed, starting_kmr, current_kmr):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if tire exists
        cursor.execute("""
        SELECT 1 FROM tires 
        WHERE tipper_id = %s AND tire_number = %s
        """, (tipper_id, tire_number))
        exists = cursor.fetchone()
        
        if exists:
            # Update existing tire
            cursor.execute("""
            UPDATE tires SET
                position = %s,
                image_paths = %s,
                condition_percent = %s,
                date_installed = %s,
                starting_kmr = %s,
                current_kmr = %s,
                last_checked = %s
            WHERE tipper_id = %s AND tire_number = %s
            """, (
                position,
                [image_path] if image_path else None,
                condition,
                date_installed,
                starting_kmr,
                current_kmr,
                datetime.now(),
                tipper_id,
                tire_number
            ))
        else:
            # Insert new tire
            cursor.execute("""
            INSERT INTO tires (
                tipper_id, tire_number, position, image_paths,
                condition_percent, date_installed, starting_kmr,
                current_kmr, last_checked
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                tipper_id,
                tire_number,
                position,
                [image_path] if image_path else None,
                condition,
                date_installed,
                starting_kmr,
                current_kmr,
                datetime.now()
            ))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        st.error(f"Database error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

# Create directories if they don't exist
os.makedirs("tire_images", exist_ok=True)

# Get tipper details
tipper_details = get_tipper_details()

# App title
st.title("🚛 Tipper Tire Management System")
st.markdown("---")

# Sidebar for navigation
menu = st.sidebar.selectbox(
    "Menu",
    ["Tire Management", "Tire Dashboard", "Tipper Info"]
)

if menu == "Tipper Info":
    st.header("ℹ️ Tipper Information")
    tipper_info_df = pd.DataFrame.from_dict(tipper_details, orient='index', columns=['Registration'])
    st.dataframe(tipper_info_df)

elif menu == "Tire Management":
    st.header("🛠️ Tire Management")
    
    # Select tipper
    selected_tipper = st.selectbox(
        "Select Tipper", 
        options=list(tipper_details.keys()),
        format_func=lambda x: f"{x} - {tipper_details[x]}",
        index=0
    )
    
    # Define all tire positions
    positions = [
        "Front Left", "Front Right",
        "Middle Left 1", "Middle Right 1",
        "Middle Left 2", "Middle Right 2",
        "Rear Left 1", "Rear Right 1",
        "Rear Left 2", "Rear Right 2"
    ]
    
    # Get existing tires for this tipper
    existing_tires = get_tires_for_tipper(selected_tipper)
    existing_tires_dict = {tire[1]: tire for tire in existing_tires}  # position: tire_data
    
    # Create a form for all tires
    with st.form("tire_management_form"):
        st.subheader(f"Tire Details for {selected_tipper} - {tipper_details[selected_tipper]}")
        
        # Create two columns for better layout
        col1, col2 = st.columns(2)
        
        for i, position in enumerate(positions):
            # Alternate between columns
            col = col1 if i % 2 == 0 else col2
            
            with col:
                st.markdown(f"### {position}")
                
                # Get existing data for this position if available
                existing_data = existing_tires_dict.get(position, None)
                
                # Tire number (fixed based on position)
                tire_number = f"Tire-{i+1}"
                st.text_input("Tire Number", value=tire_number, key=f"num_{position}", disabled=True)
                
                # Image upload
                uploaded_file = st.file_uploader(
                    f"Upload {position} Tire Image",
                    type=["jpg", "jpeg", "png"],
                    key=f"img_{position}"
                )
                
                # Display existing image if available
                if existing_data and existing_data[2] and len(existing_data[2]) > 0:
                    existing_image_path = existing_data[2][0]
                    if os.path.exists(existing_image_path):
                        try:
                            image = Image.open(existing_image_path)
                            st.image(image, caption=f"Current {position} Tire", width=200)
                        except:
                            st.warning("Could not load existing image")
                
                # Condition slider
                condition = st.slider(
                    "Condition (%)",
                    min_value=0, max_value=100, value=existing_data[3] if existing_data else 80,
                    key=f"cond_{position}"
                )
                
                # Date installed
                date_installed = st.date_input(
                    "Date Installed",
                    value=existing_data[4] if existing_data else datetime.now().date(),
                    key=f"date_{position}"
                )
                
                # KMR inputs
                col_a, col_b = st.columns(2)
                with col_a:
                    starting_kmr = st.number_input(
                        "Starting KMR",
                        min_value=0, value=existing_data[5] if existing_data else 0,
                        key=f"start_{position}"
                    )
                with col_b:
                    current_kmr = st.number_input(
                        "Current KMR",
                        min_value=starting_kmr, value=existing_data[6] if existing_data else starting_kmr,
                        key=f"current_{position}"
                    )
                
                st.markdown("---")
        
        # Submit button
        submitted = st.form_submit_button("Save All Tire Data")
        
        if submitted:
            progress_bar = st.progress(0)
            success_count = 0
            
            for i, position in enumerate(positions):
                tire_number = f"Tire-{i+1}"
                
                # Handle image upload
                uploaded_file = st.session_state.get(f"img_{position}")
                image_path = None
                
                if uploaded_file is not None:
                    # Save the uploaded file
                    ext = uploaded_file.name.split('.')[-1]
                    image_path = f"tire_images/{selected_tipper}_{tire_number}_{position.replace(' ', '_')}.{ext}"
                    with open(image_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                
                # Get other form data
                condition = st.session_state.get(f"cond_{position}")
                date_installed = st.session_state.get(f"date_{position}")
                starting_kmr = st.session_state.get(f"start_{position}")
                current_kmr = st.session_state.get(f"current_{position}")
                
                # If there's existing data but no new image uploaded, keep the existing image
                if existing_data and not uploaded_file and existing_data[2] and len(existing_data[2]) > 0:
                    image_path = existing_data[2][0]
                
                # Save to database
                if save_tire_data(
                    selected_tipper, tire_number, position, 
                    image_path, condition, date_installed, 
                    starting_kmr, current_kmr
                ):
                    success_count += 1
                
                progress_bar.progress((i + 1) / len(positions))
            
            if success_count == len(positions):
                st.success("All tire data saved successfully!")
            else:
                st.warning(f"Saved {success_count} out of {len(positions)} tires. Some updates may have failed.")

elif menu == "Tire Dashboard":
    st.header("📊 Tire Dashboard")
    
    # Select tipper
    selected_tipper = st.selectbox(
        "Select Tipper to View", 
        options=list(tipper_details.keys()),
        format_func=lambda x: f"{x} - {tipper_details[x]}",
        index=0
    )
    
    # Get tire data
    tires = get_tires_for_tipper(selected_tipper)
    
    if not tires:
        st.warning(f"No tire data available for {selected_tipper}")
    else:
        # Convert to DataFrame for visualization
        tires_df = pd.DataFrame(tires, columns=[
            'Tire Number', 'Position', 'Image Paths', 'Condition (%)',
            'Date Installed', 'Starting KMR', 'Current KMR', 'Last Checked'
        ])
        
        # Calculate KMs Run
        tires_df['KMs Run'] = tires_df['Current KMR'] - tires_df['Starting KMR']
        
        # Show summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Average Condition", f"{tires_df['Condition (%)'].mean():.1f}%")
        with col2:
            st.metric("Average KMs Run", f"{tires_df['KMs Run'].mean():,.0f} km")
        with col3:
            worst_tire = tires_df.loc[tires_df['Condition (%)'].idxmin()]
            st.metric("Worst Condition", 
                     f"{worst_tire['Condition (%)']}% ({worst_tire['Position']})",
                     delta=f"{worst_tire['KMs Run']:,.0f} km")
        
        # Visual layout of all tires
        st.subheader("Tire Positions and Conditions")
        
        # Define the tire layout (simulating a truck view)
        positions_order = [
            ["Front Left", "Front Right"],
            ["Middle Left 1", "Middle Right 1"],
            ["Middle Left 2", "Middle Right 2"],
            ["Rear Left 1", "Rear Right 1"],
            ["Rear Left 2", "Rear Right 2"]
        ]
        
        # Create columns for the visual layout
        cols = st.columns([1, 2, 2, 1])
        
        for row_idx, row_positions in enumerate(positions_order):
            for col_idx, position in enumerate(row_positions):
                # Determine which column to use (centered layout)
                display_col = cols[col_idx + 1] if len(row_positions) == 2 else cols[1]
                
                with display_col:
                    tire_data = tires_df[tires_df['Position'] == position]
                    if not tire_data.empty:
                        tire_data = tire_data.iloc[0]
                        
                        # Display tire info in a container
                        with st.container(border=True):
                            st.markdown(f"**{position}** ({tire_data['Tire Number']})")
                            
                            # Display image if available
                            if tire_data['Image Paths'] and len(tire_data['Image Paths']) > 0:
                                img_path = tire_data['Image Paths'][0]
                                if os.path.exists(img_path):
                                    try:
                                        image = Image.open(img_path)
                                        st.image(image, width=150)
                                    except:
                                        st.warning("Could not load image")
                            
                            # Display metrics
                            st.metric("Condition", f"{tire_data['Condition (%)']}%")
                            st.metric("KMs Run", f"{tire_data['KMs Run']:,.0f} km")
                            st.caption(f"Installed: {tire_data['Date Installed']}")
                    else:
                        with st.container(border=True):
                            st.markdown(f"**{position}**")
                            st.warning("No data available")
        
        # Condition trend chart
        st.subheader("Condition Overview")
        st.bar_chart(tires_df.set_index('Position')['Condition (%)'])
        
        # Tires needing attention
        critical_tires = tires_df[tires_df['Condition (%)'] < 30]
        if not critical_tires.empty:
            st.warning("⚠️ The following tires need attention:")
            st.dataframe(critical_tires[['Position', 'Tire Number', 'Condition (%)', 'KMs Run']])
