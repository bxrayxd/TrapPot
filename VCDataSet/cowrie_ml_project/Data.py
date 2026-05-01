import pandas as pd
import glob
import os
from sklearn.model_selection import train_test_split

# 1. Point to the folder containing your dataset files
data_path = '/home/MrAftrar/Study/DataSet/data' 

# 2. Get a list of all CSV files in that folder
all_files = glob.glob(os.path.join(data_path, "*.csv"))

if not all_files:
    print("❌ Error: Could not find any CSV files in the 'data' folder.")
else:
    print(f"✅ Found {len(all_files)} files. Starting merge...")
    
    li = []
    # 3. Loop through and read each file
    for filename in all_files:
        df = pd.read_csv(filename, index_col=None, header=0, low_memory=False, nrows=10000)
        li.append(df)

    # 4. Combine all dataframes into one master table
    frame = pd.concat(li, axis=0, ignore_index=True)

    print("\n--- Success! Data Merged ---")
    print(f"Total Rows: {len(frame)}")
    print("\n--- Column Names ---")
    print(frame.columns.tolist())




    # ---# --- 5. Data Cleaning: Fix the Merged Label Column ---
    weird_col = 'tunnel_parents   label   detailed-label'
    
    if weird_col in frame.columns:
        print("\n🛠️ Fixing the mashed-up label column...")
        # Split the mashed column into 3 separate columns using spaces
        # We convert it to string first just in case
        split_cols = frame[weird_col].astype(str).str.split(r'\s+', n=2, expand=True)
        
        # Assign them to their proper names
        if split_cols.shape[1] == 3:
            frame['tunnel_parents'] = split_cols[0]
            frame['label'] = split_cols[1]
            frame['detailed-label'] = split_cols[2]
            
            # Delete the old broken column
            frame.drop(columns=[weird_col], inplace=True)
            print("✅ Successfully split the columns!")
            
            print("\n--- Attack Class Distribution (General) ---")
            print(frame['label'].value_counts())
            
            print("\n--- Detailed Attack Distribution ---")
            print(frame['detailed-label'].value_counts())
        else:
            print("⚠️ Could not split perfectly. Here is a sample of the broken data:")
            print(frame[weird_col].head(5))


           # --- 6. Optimized Mapping & Feature Engineering ---

# Convert columns to numeric, forcing errors to NaN (this fixes the '-' issue)
frame['duration'] = pd.to_numeric(frame['duration'], errors='coerce').fillna(0)
frame['orig_pkts'] = pd.to_numeric(frame['orig_pkts'], errors='coerce').fillna(0)

def map_attack_type(row):
    label = str(row['detailed-label']).strip()
    
    # 1. Normal Class
    if str(row['label']).lower() == 'benign' or label == '-':
        return 'Normal'
    # 2. Scanning
    if 'PortScan' in label:
        return 'Scanning'
    # 3. Malware Download
    if 'FileDownload' in label:
        return 'Malware Download'
    # 4. Command Execution
    if label in ['C&C', 'C&C-HeartBeat', 'Okiru', 'Attack', 'DDoS']:
        return 'Command Execution'
    # 5. Brute-force (Proxy logic)
    if row['orig_pkts'] > 10 and row['duration'] < 2.0:
        return 'Brute-force'
    
    return 'Other Attack'

# Apply the mapping
frame['target'] = frame.apply(map_attack_type, axis=1)

print("\n--- Final Project Class Distribution ---")
print(frame['target'].value_counts())

# --- 7. Fast Feature Selection (VM Friendly) ---
from sklearn.preprocessing import LabelEncoder

# Keep only the most important numerical features
features = ['id.orig_p', 'id.resp_p', 'duration', 'orig_bytes', 'resp_bytes', 
            'orig_pkts', 'orig_ip_bytes', 'resp_pkts', 'resp_ip_bytes',
            'proto', 'service', 'conn_state']

X = frame[features].copy()
y = frame['target']

# Convert columns to numeric again to be safe
for col in ['orig_bytes', 'resp_bytes', 'orig_ip_bytes', 'resp_ip_bytes']:
    X[col] = pd.to_numeric(X[col], errors='coerce').fillna(0)

# Use LabelEncoder for text columns (Fast & Low Memory)
le = LabelEncoder()
for col in ['proto', 'service', 'conn_state']:
    X[col] = le.fit_transform(X[col].astype(str))

print(f"\n✅ Ready for Training. Features reduced to: {X.shape[1]}")
print(f"Memory Usage: {X.memory_usage(deep=True).sum() / 1024**2:.2f} MB")




import numpy as np
from imblearn.over_sampling import SMOTE

# --- 8. Manual Brute-force Injection ---
print("\n💉 Injecting synthetic Brute-force patterns...")

# We will create 5000 samples of Brute-force
n_samples = 5000
# Create a fake dataframe with the same columns as X
brute_force_data = pd.DataFrame(0, index=np.arange(n_samples), columns=X.columns)

# Define the "Shape" of a Brute-force attack:
brute_force_data['id.resp_p'] = 22  # Targeting SSH Port
brute_force_data['proto'] = X['proto'].mode()[0] # Usually TCP
brute_force_data['duration'] = np.random.uniform(0.1, 1.5, n_samples) # Short bursts
brute_force_data['orig_pkts'] = np.random.randint(20, 100, n_samples) # Many packets
brute_force_data['orig_bytes'] = np.random.randint(500, 2000, n_samples) # Low data
brute_force_data['service'] = X['service'].mode()[0]

# Create the labels for these 5000 rows
brute_labels = pd.Series(['Brute-force'] * n_samples)

# Add them to our main data
X_combined = pd.concat([X, brute_force_data], ignore_index=True)
y_combined = pd.concat([y, brute_labels], ignore_index=True)

# --- 9. SMOTE Balancing ---
# We filter to keep only your project's 4 main classes + Normal
target_classes = ['Scanning', 'Command Execution', 'Normal', 'Malware Download', 'Brute-force']
mask = y_combined.isin(target_classes)
X_final = X_combined[mask]
y_final = y_combined[mask]

print(f"📊 Before SMOTE: {y_final.value_counts().to_dict()}")

print("\n⚖️ Running SMOTE (Balancing classes for the VM)...")
# We set k_neighbors to 1 because 'Malware Download' is very small (70 samples)
smote = SMOTE(random_state=42, k_neighbors=5) 
X_resampled, y_resampled = smote.fit_resample(X_final, y_final)

print("\n✅ Final Balanced Dataset for Training:")
print(pd.Series(y_resampled).value_counts())

# Check Memory again
mem_mb = X_resampled.memory_usage(deep=True).sum() / 1024**2
print(f"Total Memory after SMOTE: {mem_mb:.2f} MB")





from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib # This library saves your model
import seaborn as sns
import matplotlib.pyplot as plt

# 1. Split the data
print("\n📝 Splitting data into Train (80%) and Test (20%)...")
X_train, X_test, y_train, y_test = train_test_split(X_resampled, y_resampled, test_size=0.2, random_state=42)

# 2. Train the Random Forest
rf_model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
print("🚀 Training the Random Forest (this should be fast)...")
rf_model.fit(X_train, y_train)

# 3. Evaluate
print("🔮 Evaluating the model...")
y_pred = rf_model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print(f"\n✨ SUCCESS! Model Accuracy: {accuracy * 100:.2f}%")
print("\n--- Detailed Classification Report ---")
print(classification_report(y_test, y_pred))

# 4. Save the Model and the LabelEncoder
# We need to save 'le' (LabelEncoder) so we can translate real Cowrie logs later
joblib.dump(rf_model, 'trappot_model.pkl')
joblib.dump(le, 'label_encoder.pkl')
print("\n💾 Model and Encoder saved as 'trappot_model.pkl' and 'label_encoder.pkl'")

# 5. Plot Confusion Matrix
plt.figure(figsize=(10, 7))
cm = confusion_matrix(y_test, y_pred)
sns.heatmap(cm, annot=True, fmt='d', xticklabels=rf_model.classes_, yticklabels=rf_model.classes_, cmap='Blues')
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title('TrapPot Random Forest - Confusion Matrix')
plt.savefig('confusion_matrix.png') # Saves the graph as an image in your folder
plt.show()