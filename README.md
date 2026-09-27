[Website](mnlsir.onrender.com)  
  

#### NOTE:
This is a minor documentation to help you (Prince?) wishing to continue the project from where I stopped. These information were accurate to the best of my knnowledge as at the time of writing this README file. If anything has changed, then updates may have been made to the repo without a corresponding update of the README file.  
  
Also, other things to note about the application include:  
* see env.example file for list of all environment variables required by the application
* only Admin can create new staff (thus, it is adviseable to set the role og default super user, to "Admin")
* You can set info for default super user using the environment variables SUPER_USER_NAME, SUPER_USER_PASSWORD, SUPER_USER_ROLE

  
## THE BACKEND
*The MVP features implemented as of now include*
* CRUD operations on units, products, stores etc
* Stock Taking (recording of inventory quantities)
* Goods Receiving
* issuing stock
* dispatch to vessels
* Viewing stock balances(inventory quantities of different stock)
* Viewing ledgers of Goods Received and Dispatches made
* Stock Movement records linking and updating
* Auth
* Staff management (restricted for only admin staff)


These are implemented as Service objects(see the "service" folder in the "backend" directory). Some functionality are also implemented as Repo objects (see the "repo" folder in the "backend" directory).  
  
To get a hang of how everything connects together, see the tests written in "test" folder in the "backend" directory. tests serve as examples of usage.  
  
Asides these, the data model for the entire application can be found in the file "db.py" in the "backend" directory of the application.

### THE FRONTEND  
As at the time of documenting this, the frontend work was largely aided by SQLAdmin admin pages and some generated templates (for BaseViews, which is another of sqladmin's lingo).  

Decided a monolith will be better instead of the previous idea of separately-deployed frontend and backend. Why? Note, I am subject to correction on this  
  
Well, imagine a situation where the backend is down for some reason but the frontend is still up... A staff tries to update some record using the frontend... The frontend being the frontend tries to reach the backend with no success, even after retries. It returns error-message to the staff (if the staff is patient enough to wait through the retries...), who may be in the middle of an important multi-stage activity and may not be able to persist the info somewhere offline(e.g. on paper). That info will likely be lost and impair the business process.  
  
But contrast that with a situation where everything are in one place.. if backend is down, frontend is down too.. everybody reverts to offline persistence e.g. papers and pens... to resume with online record taking whern the system gets back online