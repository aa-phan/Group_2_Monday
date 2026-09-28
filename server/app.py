# Import necessary libraries and modules
import os

from bson.objectid import ObjectId
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from pymongo import MongoClient

# Import custom modules for database interactions
import usersDatabase as usersDB
import projectsDatabase as projectsDB
import hardwareDatabase as hardwareDB

load_dotenv()

# Initialize a new Flask web application
app = Flask(__name__)


def getMongoClient():
    """Build a MongoClient from the MONGODB_URI environment variable.

    Raises RuntimeError with an actionable message when MONGODB_URI is
    unset -- there is no default connection string anywhere in this file.
    """
    uri = os.environ.get("MONGODB_URI")
    if not uri:
        raise RuntimeError(
            "MONGODB_URI is not set. Create a server/.env file (see "
            "server/requirements.txt for python-dotenv) with "
            "MONGODB_URI=<your connection string>, or export it in your shell."
        )
    return MongoClient(uri)


# Route for user login
@app.route('/login', methods=['POST'])
def login():
    # Extract data from request

    # Connect to MongoDB

    # Attempt to log in the user using the usersDB module

    # Close the MongoDB connection

    # Return a JSON response
    return jsonify({})

# Route for the main page (Work in progress)
@app.route('/main')
def mainPage():
    # Extract data from request

    # Connect to MongoDB

    # Fetch user projects using the usersDB module

    # Close the MongoDB connection

    # Return a JSON response
    return jsonify({})

# Route for joining a project
@app.route('/join_project', methods=['POST'])
def join_project():
    # Extract data from request

    # Connect to MongoDB

    # Attempt to join the project using the usersDB module

    # Close the MongoDB connection

    # Return a JSON response
    return jsonify({})

# Route for adding a new user
@app.route('/add_user', methods=['POST'])
def add_user():
    # Extract data from request

    # Connect to MongoDB

    # Attempt to add the user using the usersDB module

    # Close the MongoDB connection

    # Return a JSON response
    return jsonify({})

# Route for getting the list of user projects
@app.route('/get_user_projects_list', methods=['POST'])
def get_user_projects_list():
    # Extract data from request

    # Connect to MongoDB

    # Fetch the user's projects using the usersDB module

    # Close the MongoDB connection

    # Return a JSON response
    return jsonify({})

# Route for creating a new project
@app.route('/create_project', methods=['POST'])
def create_project():
    # Extract data from request

    # Connect to MongoDB

    # Attempt to create the project using the projectsDB module

    # Close the MongoDB connection

    # Return a JSON response
    return jsonify({})

# Route for getting project information
@app.route('/get_project_info', methods=['POST'])
def get_project_info():
    # Extract data from request

    # Connect to MongoDB

    # Fetch project information using the projectsDB module

    # Close the MongoDB connection

    # Return a JSON response
    return jsonify({})

# Route for viewing a project's hardware-set status (capacity/availability)
@app.route('/api/hardware', methods=['GET'])
def get_hardware_status():
    # Extract data from request
    projectId = request.args.get('projectId')
    userId = request.args.get('userId')

    if not projectId:
        return jsonify({"error": "missing_parameter", "field": "projectId"}), 400
    if not userId:
        return jsonify({"error": "missing_parameter", "field": "userId"}), 400

    # Connect to MongoDB
    client = getMongoClient()

    try:
        # Fetch hardware-set status using the projectsDB module
        hardwareSets = projectsDB.getProjectHardwareStatus(client, projectId, userId)
    except projectsDB.NotAHouseholdMemberError:
        return jsonify({"error": "not_a_project_member"}), 403
    except hardwareDB.ItemNotFoundError:
        return jsonify({"error": "hardware_set_not_found"}), 404
    except hardwareDB.InvalidInventoryInput as error:
        return jsonify({"error": "invalid_input", "field": str(error)}), 400
    finally:
        # Close the MongoDB connection
        client.close()

    # Return a JSON response
    return jsonify({"projectId": projectId, "hardwareSets": hardwareSets})

# Route for checking in units of a hardware set
@app.route('/api/hardware/checkin', methods=['POST'])
def checkin_hardware():
    # Extract data from request
    body = request.get_json(silent=True) or {}
    projectId = body.get('projectId')
    userId = body.get('userId')
    hwSetName = body.get('hwSetName')
    quantity = body.get('quantity')

    if not projectId:
        return jsonify({"error": "invalid_input", "field": "projectId"}), 400
    if not userId:
        return jsonify({"error": "invalid_input", "field": "userId"}), 400

    # Connect to MongoDB
    client = getMongoClient()

    try:
        # Attempt to check in the hardware set using the projectsDB module
        hardwareSet = projectsDB.checkinHardwareSet(
            client, projectId, userId, hwSetName, quantity
        )
    except projectsDB.NotAHouseholdMemberError:
        return jsonify({"error": "not_a_project_member"}), 403
    except hardwareDB.InvalidInventoryInput as error:
        return jsonify({"error": "invalid_input", "field": str(error)}), 400
    except hardwareDB.ItemNotFoundError:
        return jsonify({"error": "hardware_set_not_found"}), 404
    finally:
        # Close the MongoDB connection
        client.close()

    # Return a JSON response
    return jsonify({"hardwareSet": hardwareSet}), 201

# Route for checking out units of a hardware set
@app.route('/api/hardware/checkout', methods=['POST'])
def checkout_hardware():
    # Extract data from request
    body = request.get_json(silent=True) or {}
    projectId = body.get('projectId')
    userId = body.get('userId')
    hwSetName = body.get('hwSetName')
    quantity = body.get('quantity')

    if not projectId:
        return jsonify({"error": "invalid_input", "field": "projectId"}), 400
    if not userId:
        return jsonify({"error": "invalid_input", "field": "userId"}), 400

    # Connect to MongoDB
    client = getMongoClient()

    try:
        # Attempt to check out the hardware set using the projectsDB module
        hardwareSet = projectsDB.checkoutHardwareSet(
            client, projectId, userId, hwSetName, quantity
        )
    except projectsDB.NotAHouseholdMemberError:
        return jsonify({"error": "not_a_project_member"}), 403
    except hardwareDB.InvalidInventoryInput as error:
        return jsonify({"error": "invalid_input", "field": str(error)}), 400
    except hardwareDB.ItemNotFoundError:
        return jsonify({"error": "hardware_set_not_found"}), 404
    except hardwareDB.InsufficientStockError as error:
        return jsonify({
            "error": "insufficient_stock",
            "onHand": error.onHand,
            "requested": error.requested,
        }), 409
    except hardwareDB.ConcurrentModificationError:
        return jsonify({"error": "concurrent_modification"}), 409
    finally:
        # Close the MongoDB connection
        client.close()

    # Return a JSON response
    return jsonify({"hardwareSet": hardwareSet}), 200

# Route for requesting (reserving) a quantity of a hardware set (SN3)
@app.route('/api/hardware/request', methods=['POST'])
def request_hardware():
    # Extract data from request
    body = request.get_json(silent=True) or {}
    projectId = body.get('projectId')
    userId = body.get('userId')
    userName = body.get('userName')
    hwSetName = body.get('hwSetName')
    quantity = body.get('quantity')

    if not projectId:
        return jsonify({"error": "invalid_input", "field": "projectId"}), 400
    if not userId:
        return jsonify({"error": "invalid_input", "field": "userId"}), 400

    # Connect to MongoDB
    client = getMongoClient()

    try:
        # Attempt to request the hardware set using the projectsDB module
        reservationId, hardwareSet = projectsDB.requestHardwareSet(
            client, projectId, userId, userName, hwSetName, quantity
        )
    except projectsDB.NotAHouseholdMemberError:
        return jsonify({"error": "not_a_project_member"}), 403
    except hardwareDB.InvalidInventoryInput as error:
        return jsonify({"error": "invalid_input", "field": str(error)}), 400
    except hardwareDB.ItemNotFoundError:
        return jsonify({"error": "hardware_set_not_found"}), 404
    finally:
        # Close the MongoDB connection
        client.close()

    # Return a JSON response
    return jsonify({"reservationId": reservationId, "hardwareSet": hardwareSet}), 201

# Route for releasing a request (reservation) the caller created
@app.route('/api/hardware/release', methods=['POST'])
def release_hardware():
    # Extract data from request
    body = request.get_json(silent=True) or {}
    projectId = body.get('projectId')
    userId = body.get('userId')
    reservationId = body.get('reservationId')

    if not projectId:
        return jsonify({"error": "invalid_input", "field": "projectId"}), 400
    if not userId:
        return jsonify({"error": "invalid_input", "field": "userId"}), 400

    # Connect to MongoDB
    client = getMongoClient()

    try:
        # Attempt to release the reservation using the projectsDB module
        hardwareSet = projectsDB.releaseReservation(client, projectId, userId, reservationId)
    except projectsDB.NotAHouseholdMemberError:
        return jsonify({"error": "not_a_project_member"}), 403
    except projectsDB.ReservationNotOwnedError:
        return jsonify({"error": "not_your_reservation"}), 403
    except hardwareDB.ReservationNotFoundError:
        return jsonify({"error": "reservation_not_found"}), 404
    finally:
        # Close the MongoDB connection
        client.close()

    # Return a JSON response
    return jsonify({"hardwareSet": hardwareSet}), 200

# Main entry point for the application
if __name__ == '__main__':
    app.run(port=int(os.environ.get("PORT", 5050)))
