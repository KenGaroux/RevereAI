# Google SRE Book - Chapter 1 Notes

## Core Idea

SRE treats operations as a software engineering problem. Instead of relying only
on manual process, SRE teams build systems, automation, and feedback loops that
keep services reliable.

## Terms To Understand

- **Reliability:** the service keeps doing what users need.
- **Operations:** the work required to keep a service running.
- **Toil:** repetitive manual work that does not create lasting improvement.
- **Automation:** code or systems that reduce repeated manual work.
- **Service ownership:** engineers understand how their service behaves in real use.

## How This Applies To DEATH.AI

- Startup scripts reduce manual setup toil.
- Logs make failures easier to diagnose.
- Health endpoints show whether the system is alive.
- Memory trimming protects the model from growing context forever.
- Git history and session summaries make the project explainable later.

## Questions To Answer After Reading

1. What parts of DEATH.AI are currently toil?
2. What can be automated without hiding how the system works?
3. What should the app measure so we know it is healthy?
4. What is the simplest reliability target for a local AI app?
