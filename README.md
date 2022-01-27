# TU Darmstadt HiWi Documentation Generator
Useful helper windows application for HiWis at TU Darmstadt to create the weekly documentation of working hours. 

## Getting Started

### Download
Click the Dropdown Menu called *Clone* and select *Download ZIP* in this menu. The executable file is called `doc_generator.exe`. It won't be properly downloaded when clicking *Download ZIP* because it is too large. You have to click on this file and then download it seperately (But make sure to place it exactly where it should be located inside this directory afterwards). 

Alternatively you can *clone* this repository. For that, you'll have to install [Git Large File Storage Extension](https://git-lfs.github.com/). Don't worry, it's not that complicated. This way, the executable file is downloaded properly during the cloning process. 

Or just compile it yourself, if you know how to handle python compilers. The necessary source code is provided within this repository. You would have to point the compiler to the main file called [gui.py](./indlude/gui.py).


### Running the Application
To start the executable, just double click as you do with other windows applications.

*Hint:* This will open a terminal window first and after a little while you'll see the GUI shown below. **Don't close the terminal window**, because it will also close the application window.

### How to use it?
It is quite simple to handle the program. Just type in your personal information, the date range in between you want to generate your documentations and a weekly pattern of start and end times (Format must be HH:MM) that will be followed by the application to fill the table entries for each pdf file. The table I refer to is the one that contains the actual information about when your working time started and ended on a certain day in a week.

![image](https://user-images.githubusercontent.com/83639955/150775652-288af662-6a30-4d4f-98a2-fc54f12950b8.png)

So the pattern you have to provide could look something like that:

| Working Time Begin | Working Time End |
| --- | --- |
| 8:00 | 13:00 |
| 9:00 | 12:00 |

The total amount of hours a month will be inferred from the given pattern - Meaning `8 hours/week * 4 weeks = 32 hours/month` for the given example above. But you might want to specify that seperately. You can do so by clicking the associated Checkbox. Using this option has the advantage that you don't have to manually fit the pattern to the amount of hours a month you were or still are supposed to work. It's just less thinking you'll have to do this way. Either way, every month in between the documentation start and end will contain exactly the total amount of working hours you specified. That is until you provide implausible values (The program obviously cannot fit more hours into a month or time span than it realistically has).

This **fitting process** is the reason why the last entries of a month will differ from the pattern you provided. So don't be confused if the result doesn't look like you expected it. Just alter the pattern to better reflect the actual monthly hours. Ultimately, the amount of fitting needed depends on the pattern you provided, the documentation start and end date as well as on how many holidays there are during this documentation period.

After filling every necessary field, don't forget to select a working directory. Every pdf file will be saved there and named according to the file prefix you may provide. After that, just click `Create Files` and you will be prompted with a summary of your request. Confirm and the files will have been created in less than a second.

## Thanks for Visiting

I hope this tool will be as helpful to you as it is to me! 

Should any problems occur, please open a Git Issue with a screenshot of the console output. This will help me a lot to understand the origin of that problem.

Thanks for visiting and sharing.
