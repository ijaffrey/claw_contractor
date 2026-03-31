# Stakeholder Interview Questions

## Product Owner Interview - Testing Requirements

### Business Context & Priorities

1. **Strategic Objectives**
   - What are the top 3 business goals for the lead management system?
   - How does testing quality impact business outcomes?
   - What's the acceptable downtime/error rate from a business perspective?

2. **User Experience Priorities**
   - Which user journeys are most critical to business success?
   - What would constitute a "critical failure" from a customer perspective?
   - How quickly should the system respond to new leads?

3. **Risk Tolerance**
   - What level of testing coverage do you expect for peace of mind?
   - Are there any compliance or regulatory testing requirements?
   - What's the impact of a failed contractor notification?

### Functional Requirements Validation

4. **Email Processing**
   - How many emails per hour should the system handle?
   - What happens if Gmail API is temporarily unavailable?
   - Are there specific email formats or sources we must support?

5. **Lead Qualification**
   - How many qualification questions are typically needed?
   - What's the expected conversation length before qualification?
   - How should the system handle incomplete qualification attempts?

6. **Contractor Notifications**
   - How quickly must contractors receive lead notifications?
   - What backup notification methods should exist?
   - How do we handle contractor non-response scenarios?

### Quality & Performance Expectations

7. **Performance Standards**
   - What's the maximum acceptable response time for lead processing?
   - How many concurrent users should the web interface support?
   - What database query performance is acceptable?

8. **Reliability Requirements**
   - What system uptime percentage is required?
   - How should the system recover from failures?
   - What monitoring and alerting do you expect?

9. **Data Quality**
   - How accurate must lead parsing be (percentage)?
   - What happens if we miss a qualified lead?
   - How should data inconsistencies be handled?

### Testing Scope & Priorities

10. **Critical Test Scenarios**
    - Which test scenarios would you personally want to see?
    - What edge cases keep you up at night?
    - Which integrations are most likely to break?

11. **Test Environment**
    - Do we need production-like test data?
    - Should tests run against live Gmail/email services?
    - What test automation level do you expect?

12. **Release Confidence**
    - What testing would give you confidence to deploy?
    - How should test results be reported to stakeholders?
    - What's the acceptable test execution time?

## Technical Team Interview Questions

### Architecture & Integration Points

13. **System Dependencies**
    - Which external services are most fragile?
    - What authentication/security testing is needed?
    - Are there any known performance bottlenecks?

14. **Database Concerns**
    - What database migration testing is required?
    - How should we handle test data cleanup?
    - Are there specific query performance requirements?

15. **API & Interface Testing**
    - Which API endpoints are most complex?
    - What error scenarios should we test?
    - How should we mock external dependencies?

### Development Workflow

16. **Test Integration**
    - How should tests fit into the CI/CD pipeline?
    - What's the expected test execution time?
    - Should tests block deployments on failure?

17. **Maintenance & Updates**
    - How often should test data be refreshed?
    - What test documentation is needed?
    - How should test failures be triaged?

## Operations Team Interview Questions

### Monitoring & Observability

18. **Production Monitoring**
    - What metrics should tests validate?
    - How should test environments mirror production?
    - What logging/tracing testing is needed?

19. **Deployment & Rollback**
    - What deployment testing is required?
    - How should rollback scenarios be tested?
    - What infrastructure testing do you need?

20. **Capacity Planning**
    - What load testing scenarios are important?
    - How should we test system scaling?
    - What resource utilization should we monitor?

## Interview Schedule

### Primary Stakeholder (Product Owner)
**Duration:** 60 minutes
**Focus:** Business requirements, priorities, acceptance criteria
**Questions:** 1-12

### Technical Lead
**Duration:** 45 minutes  
**Focus:** Architecture, integration, development workflow
**Questions:** 13-17

### DevOps/Operations Lead
**Duration:** 30 minutes
**Focus:** Infrastructure, monitoring, deployment
**Questions:** 18-20

## Expected Outcomes

### Requirements Clarification
- Specific performance benchmarks
- Risk tolerance levels
- Critical vs. nice-to-have functionality
- Test coverage expectations

### Scope Refinement
- Priority test scenarios
- Resource allocation
- Timeline expectations
- Success criteria definition

### Stakeholder Alignment
- Shared understanding of quality goals
- Clear acceptance criteria
- Agreed testing approach
- Communication preferences
