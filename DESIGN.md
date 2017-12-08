- heroku server:
    We use Heroku to host the website database because the CS50 IDE cannot host the website all the time.
    Heroku is free server service. We first setup our website data in CS50 IDE environment, then we use GitHub
    synchronize all the data on CS50 IDE. Finally, in the Heroku, we set the data to connect GitHub. In this way,
    everythinh we implement in CS50 IDE will synchronize to GitHub. And the Heroku will get all the updated
    data by connecting GitHub. In other words, Github bridge the CS50 IDE and Heroku. By doing this, we can test
    pur website locally(we can use "flask run" under CS50 IDE) and examine the problems. When all things worked well,
    we published the project data to GitHub. Heroku can fetch the latest data from GitHub.

- python app
    Application.py has routes to redirect html pages. Here, there are not too many functions to apply to website.
    We use python to direct the routes of the website.

- javascript D3 framework
    For the data viualization, we use D3, java library, to bring data to HTML. D3 provides a javascript library rpovide examples
    for visualizing data. We referenced the D3 library, and used javascript to process the data. All input data format are as CSV,
    we took CSV file and used javascript to generate the graph. The reason that we used CSV is that most of the simulaiotn results
    can be exported into CSV format. We don't need to reformat the simulaiton results.

