# Assessment data

The application and dataset-backed tests read `../data data.csv` directly. This is the unchanged 40,000-employee assessment attachment.

Employee Id and Manager define reporting relationships. Name, Department, Job Title and Location populate employee details. Salary is annual base pay; each value rounds half-up to cents before aggregation. Bonus is excluded. The source has no currency column, so amounts are labeled as unspecified currency.

Verification and benchmark scripts write local outputs here. Those outputs are ignored by Git.
