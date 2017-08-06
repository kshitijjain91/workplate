# Project Workplate

Project workplate is a lightweight web app created for (mainly junior level) employees to keep track of their daily
office tasks.

It is deployed at the following URLs:
- www.workplate.in
- www.workplate.co

The obective is to make it extremely easy for people to know 1) what tasks they should have had done already, 2) what they have to do 'by today' and 3) what is due tomorrow or later.


Thus, all tasks fall into either of the three buckets - 1) overdue, 2) due today and 3) to be done later.

## Assigned by and Assigned to

Most tasks are assigned by other people, such as one's manager, a marketing fellow who wants a PPT 'asap' etc.
These fall into 'Assigned by X' category. Any assigned task will either be overdue, due today or due later.

The tasks assigned to others fall in 'Assigned to X', and one may assign a task to himself/herself also (which may be the person's TO-DO list).


## Example Use Case

Narayana, a new intern in the office, works on two projects - a) A data analysis project led by Ravi, the marketing manager and b) day to day tasks of the content team where there's no one person managing him, though Prateek and CJ assign most tasks (such as uploading content, reviewing some code, sourcing some good blog posts on python etc.).

To make things clear for Narayana, Ravi, Prateek and CJ can simply assign the tasks to him specifying what needs to be done and by when. Also, each task is inside a 'project'.

For e.g. Ravi may assign 'Make data dictionary by Wednesday', 'Clean the data by Thursday afternoon' and 'Source college data by Thursday EOD'. CJ assigns him 'Upload module 1 by Wednesday afternoon' and 'Send blogs by Thursday afternoon.' Optionally, the assigner can also mention the estimated time taken for the task.

On Wednesday, Narayana's "Assigned by" dashboard will show three components:
1) Overdue: Anything due from Tuesday or before
2) Due today:
    - Data dictionary, by Ravi, by EOD
    - Upload module 1, by CJ, by afternoon
3) Due tomorrow:
    - Clean data, by Ravi, by afternoon
    - Source college data, by Ravi, by EOD
    - Send python blogs, by CJ, by afternoon

Now if Prateek also assigns something to Narayana to be done by Wed afternoon, he'll be notified by the app that 'Narayana seems to have 3 due tasks by Wednesday, do you want to consider pushing this one?'. If Prateek pushes it to a later date, well and good, else Narayana cannot push it himself (the app assumes that the assigner has taken a deliberate call.)


Ravi, CJ and Prateek will have the same tasks in their 'Assigned to Narayana' showing in assigned-by-you/overdue/due-today/due-on-X.


## Apart from daily tasks

Apart from daily tracking of tasks, the app can also be used by teams to track metrics such as the aggregate amount of 'total overdue-tasks', the aggregate number of overdue tasks of each person etc.

### Pages

1. Home (or dashboard)
    - Two main sections in the header: Assigned to you and assigned by you
    - Project: Panel on the left showing the list of projects a person is a part of
    - 3 states: Overdue, Due Today and Due Tomorrow

2. Assigned to you page
    - List of tasks showing description, assigned by and due date-time
    - Task action: Move task to Done

3. Assigned by you page
    - List of tasks showing description, assigned to and due date-time
    - Assign new task
    - Task action: Change due date / delete task










