"""
Flask web application for RoomSizer wallpaper calculator.
Provides a simple web UI for calculating wallpaper needs.
"""

from flask import Flask, render_template, request, jsonify
from roomsizer.domain import Room, Opening, OpeningKind, WastePolicy, Wallpaper

app = Flask(__name__)


@app.route('/')
def index():
    """Render the main calculator page."""
    return render_template('index.html')


@app.route('/calculate', methods=['POST'])
def calculate():
    """
    Calculate wallpaper rolls needed based on user input.

    Expected JSON payload:
    {
        "room": {"width": float, "length": float, "height": float},
        "rollWidth": float,
        "rollLength": float,
        "dropAllowance": float,
        "extraFactor": float,
        "openings": [{"width": float, "height": float, "kind": "WINDOW"|"DOOR"}, ...]
    }

    Returns:
    {
        "success": true,
        "rollsNeeded": int,
        "wallArea": float,
        "netWallArea": float,
        "perimeter": float
    }
    or
    {
        "success": false,
        "error": string
    }
    """
    try:
        data = request.get_json()

        # Validate required fields
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        # Extract room data
        room_data = data.get('room', {})
        room_width = float(room_data.get('width', 0))
        room_length = float(room_data.get('length', 0))
        room_height = float(room_data.get('height', 0))

        # Extract wallpaper roll data
        roll_width = float(data.get('rollWidth', 0))
        roll_length = float(data.get('rollLength', 0))

        # Extract waste policy data
        drop_allowance = float(data.get('dropAllowance', 0))
        extra_factor = float(data.get('extraFactor', 1.0))

        # Create room
        room = Room(width=room_width, length=room_length, height=room_height)

        # Add openings
        openings_data = data.get('openings', [])
        for opening_data in openings_data:
            opening_width = float(opening_data.get('width', 0))
            opening_height = float(opening_data.get('height', 0))
            opening_kind_str = opening_data.get('kind', 'WINDOW').upper()

            # Convert string to OpeningKind enum
            opening_kind = OpeningKind.WINDOW if opening_kind_str == 'WINDOW' else OpeningKind.DOOR

            opening = Opening(width=opening_width, height=opening_height, kind=opening_kind)
            room.add_opening(opening)

        # Create waste policy
        policy = WastePolicy(drop_allowance=drop_allowance, extra_factor=extra_factor)

        # Calculate wallpaper needs
        wallpaper = Wallpaper(
            roll_width=roll_width,
            roll_length=roll_length,
            room=room,
            policy=policy
        )

        rolls_needed = wallpaper.rolls_needed()

        # Return results with additional information
        return jsonify({
            "success": True,
            "rollsNeeded": rolls_needed,
            "wallArea": round(room.wall_area(), 2),
            "netWallArea": round(room.net_wall_area(), 2),
            "perimeter": round(room.perimeter(), 2)
        })

    except ValueError as e:
        # Domain validation errors
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        # Unexpected errors
        return jsonify({"success": False, "error": f"Unexpected error: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
