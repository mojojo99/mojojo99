# AI Pre-Survey: setup guide

About 20 minutes, done once. After that, each new class only needs a new class code.

What you end up with:
- A Microsoft Form that clients fill in. They see a thank-you message and no score.
- An email in your work inbox for every submission. It contains the participant's full answers plus the running group result for their class.
- A "Group Summary" tab in the Excel workbook that updates itself, with one row per class code.

All files are in your OneDrive, in the **AI Pre-Survey** folder.

## A. Create the form (about 5 minutes)

1. Go to forms.office.com, click the arrow next to **New Form**, and choose **Quick import**.
2. Pick **AI Pre-Survey - Forms import.docx** from OneDrive. When asked, choose **Form**, not Quiz. A quiz would show participants their scores.
3. Check the imported questions and set them up as follows:
   - Q1 Class code, Q2 Full name, Q3 Email: turn **Required** on. For Q3, open **…** → **Restrictions** → **Email**.
   - Q5: a single-answer Choice question. Make it Required.
   - Q6: a Choice question. Turn **Multiple answers** on.
   - Q7 to Q18: the 12 confidence ratings. Make each one Required. They work as imported (choices 1 to 5). If you'd rather show a row of numbers, change each to **Rating → Number, 5 levels**. The script reads either format.
   - Q19 and Q20: Text questions. Turn **Long answer** on.
4. Open **… → Settings**:
   - Who can fill out this form: **Anyone can respond**. Your clients are outside your organisation.
   - Turn **Customize thank you message** on and paste in: *Thank you! Your answers help us shape the sessions for your group. See you in class.*
   - Leave **Get email notification of each response** off. The flow sends a better email.
5. Use **Collect responses** to get the link. Never share the **Results** or summary link with clients.

## B. Add the script to the workbook (about 3 minutes)

1. Open **AI Pre-Survey Responses.xlsx** in Excel for the web.
2. Go to the **Automate** tab → **New Script**. Delete the sample code and paste in everything from **PreSurveyIntake.ts**.
3. Rename the script **PreSurveyIntake** and click **Save**.

Leave the "Responses" table's first empty row in place. The script fills it with the first response.

## C. Build the flow (about 10 minutes)

1. Go to make.powerautomate.com → **Create** → **Automated cloud flow**. Name it *AI Pre-Survey intake*. Choose the trigger **When a new response is submitted** (Microsoft Forms), then **Create**.
2. **Trigger**, Form Id: pick *AI Training Pre-Survey*.
3. **Add an action → Microsoft Forms → Get response details**
   - Form Id: the same form.
   - Response Id: the dynamic value **Response Id**. If Power Automate wraps this in "Apply to each", that's fine. Put the next two actions inside it.
4. **Add an action → Excel Online (Business) → Run script**
   - Location: OneDrive for Business. Document Library: OneDrive. File: */AI Pre-Survey/AI Pre-Survey Responses.xlsx*. Script: **PreSurveyIntake**.
   - Fill in each parameter from the "Get response details" dynamic content:

     | Script field | Form answer |
     |---|---|
     | submitted | Submission time |
     | classCode | Class code |
     | name | Your full name |
     | email | Your email address |
     | role | Your role and organisation |
     | aiUse | How often do you use AI tools… |
     | tools | Which of these AI tools have you used? |
     | q1 … q12 | The 12 "How confident are you…" questions, in order |
     | task | What is one task in your week… |
     | goal | By the end of the training… |

5. **Add an action → Office 365 Outlook → Send an email (V2)**
   - To: your work address.
   - Subject: the dynamic value **subject** (from Run script).
   - Body: click the **</>** code-view button first, then insert the dynamic value **html** (from Run script).
6. **Save**, then **Test → Manually**. Submit one test response using class code **TEST**.

You should get an email within a minute or two, and see a TEST row in both the Responses and Group Summary tabs. Delete the TEST row from **Responses**. The Group Summary rebuilds itself from Responses at the next submission.

## D. Running a class

- Give each class its own code, e.g. ACME-NOV. Codes are not case-sensitive.
- Share the form link before the first session.
- Before you plan the session, read that class's row in **Group Summary**:
  - **Suggested cohort start:** the first level the group average hasn't reached (3.5 out of 5).
  - **People at L1 / L2 / L3 / L3+:** how spread out the group is.
  - **Group note:** flags a mixed group, where less than 60% of people sit at the same level.
  - **Most used tools:** helps you pick demo tools the group already knows.
- The Responses tab also has a "Suggested level" column for each person. Only you see it.

## If something goes wrong

- **Run script can't see the parameters:** open the script in Excel, save it again, then pick the script again in the flow.
- **Ratings are blank in the sheet:** check that q1–q12 are mapped to the rating questions, in order.
- **No email arrives:** open the flow's **Run history** to see which step failed.
