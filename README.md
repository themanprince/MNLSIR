#### NOTE:
This is a minor documentation to help you (Prince?) wishing to continue the project from where I stopped. These information were accurate to the best of my knnowledge as at the time of writing this README file. If anything has changed, then updates may have been made to the repo without a corresponding update of the README file.  
  
Also, other things to note about the application include:  
* only Admin can create new staff (thus, it is adviseable to set default super user's role to Admin)
* You can set info for default super user using the environment variables SUPER_USER_NAME, SUPER_USER_PASSWORD, SUPER_USER_ROLE
* see env.example file for list of all environment variables required by the application
  
## THE BACKEND
*The MVP features implemented as of now include*
* Stock Taking (inventory quantities recording)
* Goods Receiving
* issuing stock
* Viewing stock balances(inventory quantities of different stock)

These are implemented as Service objects(see the "service" folder in the "backend" directory). Some functionality can also be implemented as Repo objects (see the "repo" folder in the "backend" directory). To get a hang of how they are used, see the tests written in "test" folder in the "backend" directory.

The endpoints for accessing and using these services were being developed side by side the frontend of the application. To implement a single route, I usually had to
* create custom exception/error objects that could be raised (see "exceptions.py" file in "backend" folder)
* create custom schema objects for input/output to/fro the routes (or sometimes use primitives too for data transfer)
* create the route handler object (see the "endpoints" folder in the "backend" directory)
* add the route handler object to the application using the .include_router() method of the main application instance in the file "main.py" in the "backend" directory
  
Asides these, the data model for the entire application can be found in the file "db.py" in the "backend" directory of the application.

### THE FRONTEND
The _'view"_ sub-endpoints handle the template rendering for the frontend of the application.  
  
Decided a monolith will be better instead of the previous idea of separately-deployed frontend and backend. Why?  
  
Imagine a situation where the backend is down for some reason but the frontend is still up... A staff tries to update some record using the frontend... The frontend being the frontend tries to reach the backend with no success, even after retries. It returns error-message to the staff (if the staff is patient enough to wait through the retries...), who may be in the middle of an important multi-stage activity and may not be able to persist the info somewhere offline(e.g. on paper). That info will likely be lost and impair the business process.  
  
But contrast that with a situation where everything de one place.. if backend is down, frontend is down too.. everybody reverts to offline persistence e.g. papers and pens... to resume with online record taking whern the system gets back online