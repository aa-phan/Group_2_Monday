# Import necessary libraries and modules
import hardwareDatabase as hardwareDB
import projectsDatabase as projectsDB
from passwordSecurity import InvalidPasswordError, hashPassword, verifyPassword

'''
Structure of User entry:
User = {
    'username': username,
    'userId': userId,
    'password': password,   # bcrypt hash -- plaintext is never stored (SR3)
    'projects': [project1_ID, project2_ID, ...]
}
'''

# Reuse hardwareDatabase's DB_NAME (same convention as projectsDatabase.py)
# rather than defining a second MONGODB_DB default here -- users, projects,
# and hardware sets must all land in the same database.
DB_NAME = hardwareDB.DB_NAME
USERS_COLLECTION = "Users"


class UserAlreadyExistsError(Exception):
    """Raised by addUser when userId is already taken."""


# Function to add a new user
def addUser(client, username, userId, password):
    """Create a new user, storing a bcrypt hash of password, never the
    plaintext itself.

    Raises InvalidPasswordError (from passwordSecurity) if password fails
    validation, or UserAlreadyExistsError if userId is already taken.
    """
    hashedPassword = hashPassword(password)  # raises InvalidPasswordError

    collection = client[DB_NAME][USERS_COLLECTION]

    if collection.find_one({"userId": userId}) is not None:
        raise UserAlreadyExistsError(userId)

    collection.insert_one({
        "username": username,
        "userId": userId,
        "password": hashedPassword,
        "projects": [],
    })


# Helper function to query a user by username and userId
def __queryUser(client, username, userId):
    # Query and return a user from the database
    collection = client[DB_NAME][USERS_COLLECTION]
    return collection.find_one({"username": username, "userId": userId})


# A hash of a value nobody will ever actually submit as a password, used
# only to give the "no such user" path in login() a bcrypt comparison to
# run -- so it costs roughly the same time as a real wrong-password check
# and a failed login can't be used to enumerate valid userIds by timing.
_DUMMY_HASH = hashPassword("no-such-user-placeholder")


# Function to log in a user
def login(client, username, userId, password):
    """Authenticate a user against their stored bcrypt hash.

    Returns True on success, False for any mismatch -- unknown
    username/userId and wrong password are indistinguishable to the
    caller, on purpose.
    """
    user = __queryUser(client, username, userId)
    if user is None:
        verifyPassword(password, _DUMMY_HASH)
        return False

    return verifyPassword(password, user["password"])


class UserNotFoundError(Exception):
    """Raised when a userId does not exist."""


def getUser(client, userId):
    """Return {username, userId, projects} for userId, or None. Never
    includes the password hash. A non-str userId returns None without
    reaching Mongo (operator-injection guard).
    """
    if not isinstance(userId, str):
        return None

    user = client[DB_NAME][USERS_COLLECTION].find_one({"userId": userId})
    if user is None:
        return None

    return {
        "username": user["username"],
        "userId": user["userId"],
        "projects": list(user.get("projects", [])),
    }


# Function to add a user to a project
def joinProject(client, userId, projectId):
    """Add userId to the project and the project to the user (both
    idempotent). Returns the project summary.

    Raises UserNotFoundError, or projectsDB.ProjectNotFoundError before any
    write to the user document.
    """
    if getUser(client, userId) is None:
        raise UserNotFoundError(userId)

    projectsDB.addUser(client, projectId, userId)

    client[DB_NAME][USERS_COLLECTION].update_one(
        {"userId": userId}, {"$addToSet": {"projects": projectId}}
    )

    return projectsDB.queryProject(client, projectId)


# Function to get the list of projects for a user
def getUserProjectsList(client, userId):
    """Return summaries of the user's projects. Membership is read from the
    projects' users lists (the source of truth).
    """
    if getUser(client, userId) is None:
        raise UserNotFoundError(userId)

    return projectsDB.listProjectsForUser(client, userId)
