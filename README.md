#### NOTE:
This is a minor documentation to help you (Prince?) wishing to continue the project from where I stopped. These information were accurate to the best of my knnowledge as at the time of writing this README file. If anything has changed, then updates may have been made to the repo without a corresponding update of the README file.  

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
Let me start by saying I am no UI/UX Designer. I needed assistance with the aestheticsc of the application and employed the help of AI and permit me to say I am very disaappointed. Not with the aesthetics because it did that well. However, the code has required much rewriting, bug-fixes etc.

The functionalities implemented are simply Read/Create functionalities for Products, Stores, Units, StockBalances.
There is a file named "api.js" in "src" folder of the "frontend" directory which handles the communication witht the backend.
However, I will prefer the frontend re-written, maybe the reusable components in "src/components" could be reused for redeveloping it.