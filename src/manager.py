import json
import os
import shutil
from pathlib import Path
from typing import List, Optional, Tuple
import logging
from .models import Trip

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TripManager:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_folder_name(self, trip: Trip) -> str:
        """Generates a folder name based on trip date and location."""
        city = trip.city.strip().replace(" ", "_")
        country = trip.country.strip().replace(" ", "_")
        return f"{trip.start_date}_{city}_{country}"

    def scan_trips(self) -> List[Trip]:
        """Scans the base_path for trip folders and loads metadata."""
        trips = []
        if not self.base_path.exists():
            return trips

        for folder in self.base_path.iterdir():
            if folder.is_dir():
                metadata_path = folder / "metadata.json"
                if metadata_path.exists():
                    try:
                        with open(metadata_path, 'r') as f:
                            data = json.load(f)
                            trips.append(Trip.from_dict(data))
                    except Exception as e:
                        logger.warning(f"Failed to load trip from {folder}: {e}")
        
        # Sort trips by start date descending
        trips.sort(key=lambda x: x.start_date, reverse=True)
        return trips

    def save_trip(self, trip: Trip, uploaded_files: List = []) -> bool:
        """Saves a trip and its attachments to the file system. Handles renaming if date/location changed."""
        try:
            # Check if we are updating an existing trip that might need a folder rename
            existing_trip = self.get_trip_by_id(trip.id)
            if existing_trip:
                old_folder_name = self._get_folder_name(existing_trip)
                new_folder_name = self._get_folder_name(trip)
                
                if old_folder_name != new_folder_name:
                    old_path = self.base_path / old_folder_name
                    new_path = self.base_path / new_folder_name
                    if old_path.exists():
                        # If new path already exists (collision), we might need to be careful.
                        # For now, we'll just move.
                        if not new_path.exists():
                            shutil.move(str(old_path), str(new_path))
                        else:
                            # Collision! Just copy data over or merge.
                            # For now, we'll try to merge.
                            for item in old_path.iterdir():
                                dest = new_path / item.name
                                if not dest.exists():
                                    shutil.move(str(item), str(dest))
                            shutil.rmtree(old_path)

            folder_name = self._get_folder_name(trip)
            trip_dir = self.base_path / folder_name
            trip_dir.mkdir(parents=True, exist_ok=True)

            # Handle attachments
            new_attachments = []
            for uploaded_file in uploaded_files:
                file_path = trip_dir / uploaded_file.name
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                if uploaded_file.name not in trip.attachments:
                    new_attachments.append(uploaded_file.name)
            
            # Merge with existing attachments
            trip.attachments = list(set(trip.attachments + new_attachments))

            # Save metadata
            metadata_path = trip_dir / "metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(trip.to_dict(), f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Error saving trip: {e}")
            return False

    def delete_trip(self, trip_id: str) -> bool:
        """Deletes a trip folder matching the given ID."""
        try:
            for folder in self.base_path.iterdir():
                if folder.is_dir():
                    metadata_path = folder / "metadata.json"
                    if metadata_path.exists():
                        with open(metadata_path, 'r') as f:
                            data = json.load(f)
                            if data.get("id") == trip_id:
                                shutil.rmtree(folder)
                                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting trip {trip_id}: {e}")
            return False

    def get_trip_by_id(self, trip_id: str) -> Optional[Trip]:
        """Finds a trip by its unique ID."""
        for trip in self.scan_trips():
            if trip.id == trip_id:
                return trip
        return None

    def get_attachment_path(self, trip: Trip, filename: str) -> Path:
        """Returns the full path to an attachment."""
        folder_name = self._get_folder_name(trip)
        return self.base_path / folder_name / filename
