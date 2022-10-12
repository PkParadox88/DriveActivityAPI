from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.activity']


def main():
    """Shows basic usage of the Drive Activity API.

    Prints information about the last 10 events that occured the user's Drive.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('driveactivity', 'v2', credentials=creds)

    # Call the Drive Activity API
    try:
        results = service.activity().query(body={
            'pageSize':20
            #"filter": "time >= \"2022-09-15T00:00:00-05:00\""
        }).execute()
        activities = results.get('activities', [])

        if not activities:
            print('No activity.')
        else:
            print('#Time\t*\t#Action\t*\t#ActorID\t*\t#DocumentID\t*\t#OwnerID')

            for activity in activities:

                time = getTimeInfo(activity)
                action = getActionInfo(activity['primaryActionDetail'])
                actors = map(getActorInfo, activity['actors'])
                targets = map(getTargetInfo, activity['targets'])
                actors_str, targets_str = "", ""
                actor_name = actors_str.join(actors)
                target_name = targets_str.join(targets)

                # Print the action occurred on drive with actor, target item and timestamp
                print(time+"\t*\t"+action +"\t*\t"+ actor_name +"\t*\t" +target_name)

    except HttpError as error:
        # TODO(developer) - Handleerrors from drive activity API.
        print(f'An error occurred: {error}')


# Returns the name of a set property in an object, or else "unknown".
def getOneOf(obj):
    for key in obj:
        return key
    return 'unknown'


# Returns a time associated with an activity.
def getTimeInfo(activity):
    if 'timestamp' in activity:
        return activity['timestamp']
    if 'timeRange' in activity:
        return activity['timeRange']['endTime']
    return 'unknown'


# Returns the type of action and details.
def getActionInfo(actionDetail):
    action = getOneOf(actionDetail)
    if 'create' in actionDetail:
        action = "create:"+getOneOf(actionDetail['create'])
    if 'permissionChange' in actionDetail:
        PermissionChangeObj = actionDetail['permissionChange']

        action = "PermissionChange"
        if 'addedPermissions' in PermissionChangeObj:
            role = map(getPermissionRoleInfo,PermissionChangeObj['addedPermissions'])
            role_a = ""
            role_a = role_a.join(role)
            action = action + "-to:" + role_a


            userInfo = map(getPermissionChangeUserInfo,PermissionChangeObj['addedPermissions'])

        if 'removedPermissions' in PermissionChangeObj:
            role = map(getPermissionRoleInfo,PermissionChangeObj['removedPermissions'])
            role_r = ""
            role_r = role_r.join(role)
            action = action + "-from:" + role_r

            userInfo = map(getPermissionChangeUserInfo, PermissionChangeObj['removedPermissions'])

        user_I = ""
        user_I = user_I.join(userInfo)
        action = action + "-for:" + user_I

    return action

# Return the user role for Permission change action
def getPermissionRoleInfo(PermissionObj):
    return PermissionObj.get('role')

# Return the affected user ID for Permission change action
def getPermissionChangeUserInfo(PermissionObj):
    return getUserInfo(PermissionObj['user'])


# Returns user information, or the type of user if not a known user.
def getUserInfo(user):
    if 'knownUser' in user:
        userID = user['knownUser'].get('personName')
        userIDs = userID.split('/')
        userID = userIDs[1]
        return (userID)
    return getOneOf(user)


# Returns actor information, or the type of actor if not a user.
def getActorInfo(actor):
    if 'user' in actor:
        return getUserInfo(actor['user'])
    return getOneOf(actor)


# Returns the information about target: Document ID, Name and Owner.
def getTargetInfo(target):
    if 'driveItem' in target:
        name = target['driveItem'].get('name', 'unknown')
        names = name.split('/')
        name = names[1]


        # Get the owner information
        driveItemObj  = target['driveItem']
        ownerObj = driveItemObj['owner']

        ownerID = "Unknown"
        if 'user' in ownerObj:
            ownerID = getUserInfo(ownerObj['user'])


        return '{0}\t*\t{1}'.format(name,ownerID)
    return '{0}:unknown'.format(getOneOf(target))


if __name__ == '__main__':
    main()