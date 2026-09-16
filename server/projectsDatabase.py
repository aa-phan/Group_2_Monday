# Import necessary libraries and modules
from pymongo import MongoClient

import hardwareDatabase as hardwareDB

'''
Structure of Project entry:
Project = {
    'projectName': projectName,
    'projectId': projectId,
    'description': description,
    'hwSets': {HW1: 0, HW2: 10, ...},
    'users': [user1, user2, ...]
}

Item-stock shape (Track B) is superseded by hardwareDatabase's own
docstring: household inventory now lives in the separate `Items`
collection (householdId + location + itemKey), not nested in this
document. This document's `users` list remains the source of truth for
household membership; see assertHouseholdMember below.
'''

# Function to query a project by its ID
def queryProject(client, projectId):
    # Query and return a project from the database
    pass

# Function to create a new project
def createProject(client, projectName, projectId, description):
    # Create a new project in the database
    pass

# Function to add a user to a project
def addUser(client, projectId, userId):
    # Add a user to the specified project
    pass

# Function to update hardware usage in a project
def updateUsage(client, projectId, hwSetName):
    # Update the usage of a hardware set in the specified project
    pass

# Function to check out hardware for a project
def checkOutHW(client, projectId, hwSetName, qty, userId):
    # Check out hardware for the specified project and update availability
    pass

# Function to check in hardware for a project
def checkInHW(client, projectId, hwSetName, qty, userId):
    # Check in hardware for the specified project and update availability
    pass


# ---------------------------------------------------------------------------
# Track B — household inventory (food-item stock)
#
# Inventory lives in the separate `Items` collection (hardwareDatabase.py),
# keyed by householdId + location + itemKey. This section reads the
# `Households` collection only to check membership (`users` list); it never
# reads or writes household document fields Track A owns (projectName,
# hwSets, etc. above).
# ---------------------------------------------------------------------------


class NotAHouseholdMemberError(Exception):
    """Raised when userId is not a member of the household. Maps to HTTP 403."""


def assertHouseholdMember(client, householdId, userId):
    """Trust-boundary guard: raise NotAHouseholdMemberError unless userId is
    a member of the household identified by householdId. Every inventory
    route calls this first, before touching any stock.
    """
    db = client[hardwareDB.DB_NAME]
    household = db[hardwareDB.HOUSEHOLDS_COLLECTION].find_one({"householdId": householdId})

    if household is None or userId not in household.get("users", []):
        raise NotAHouseholdMemberError(userId)


def restockItem(client, householdId, userId, location, itemName, quantity, purchaseDate, bestByDate):
    """Append a new batch to an item after verifying household membership."""
    assertHouseholdMember(client, householdId, userId)
    return hardwareDB.addBatch(client, householdId, location, itemName, quantity, purchaseDate, bestByDate)


def getHouseholdInventory(client, householdId, userId):
    """Return the household's inventory grouped by location after verifying
    household membership.
    """
    assertHouseholdMember(client, householdId, userId)
    return hardwareDB.getItemsByLocation(client, householdId)

