# Code Review Guidelines

## Review Process
1. **Self Review**: Author reviews own changes first
2. **Peer Review**: At least one team member review
3. **Testing**: All tests must pass via import validation
4. **Documentation**: Update relevant documentation

## Review Checklist
- [ ] Code follows established standards
- [ ] Tests are included and pass
- [ ] Documentation is updated
- [ ] No secrets or credentials committed
- [ ] Import-only test validation passes
- [ ] Error handling is appropriate
- [ ] Performance implications considered

## Review Focus Areas
- **Functionality**: Does the code do what it's supposed to?
- **Maintainability**: Is the code readable and well-structured?
- **Security**: Are there any security vulnerabilities?
- **Performance**: Are there any performance issues?
- **Testing**: Are the tests comprehensive and meaningful?

## Approval Criteria
- All checklist items completed
- No blocking issues identified
- Tests pass via import validation
- Documentation updated as needed

## Security Review
- No hardcoded credentials or secrets
- Environment variables used properly
- Input validation implemented
- SQL injection prevention

## Testing Review
- Import-only validation passes
- Test coverage maintained
- Mock usage appropriate
- Edge cases considered
