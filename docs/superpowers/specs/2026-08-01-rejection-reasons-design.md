# F3 Rejection Reasons Design Spec

> **Goal:** Enable structured capture and display of rejection reasons when applications are rejected, integrated with timeline events and displayed in both pipeline move dialogs and application workspaces.

## Context

Based on user preferences from brainstorming:
- **Scope:** Basic rejection reasons capture
- **Input Locations:** Both pipeline move dialog and application workspace
- **Storage:** Timeline-only approach (leverage existing REJECTED timeline events)
- **Categories:** Keep existing enum (visa_sponsorship, lack_of_experience, salary, culture_fit, position_filled, no_feedback, other)
- **Display:** Both timeline integration and dedicated workspace section
- **Validation:** Optional capture (category and reason text both optional)

## Current State

**Existing Infrastructure:**
- ✅ Timeline events system (F2) with REJECTED event type
- ✅ Applications table has `rejection_reason_category` enum field
- ✅ Timeline events support custom summary, note, and importance levels
- ✅ Pipeline stage move functionality exists
- ✅ Application workspace UI with timeline display

**Gaps to Fill:**
- Rejection reason capture during pipeline stage moves
- Rejection reason editing in application workspace
- Display rejection reasons in timeline with category badges
- Dedicated rejection section in workspace
- Backend support for rejection metadata in timeline events

## Architecture

### Data Model Approach: Timeline-Only

Leverage the existing timeline events system to store rejection details:

**Timeline Event Enhancement:**
- When application moves to Rejected stage → Create REJECTED timeline event
- Store rejection reason category in event metadata or separate field
- Store free-text rejection reason in event `note` field
- Use existing `summary` field for display ("Rejected — [Category]")

**Rationale:**
- Avoids schema changes to applications table
- Maintains chronological history (rejection is an event)
- Leverages existing timeline infrastructure
- Enables analytics via timeline event queries
- Cleaner separation of concerns

### Backend Components

**Enhanced Timeline Events:**
- Add `rejection_reason_category` field to TimelineEvent model (nullable)
- Update timeline event creation logic for REJECTED events
- Ensure rejection reasons sync from timeline to applications table

**Application Service Updates:**
- Update stage change logic to capture rejection reasons
- Add rejection reason editing capabilities
- Maintain backward compatibility

### Frontend Components

**Pipeline Move Dialog Enhancement:**
- Add rejection reason capture when moving to Rejected stage
- Category dropdown with existing enum values
- Optional free-text reason field
- Clean integration with existing move dialog

**Application Workspace Enhancement:**
- Add rejection details section (shown when status = rejected)
- Edit rejection reasons post-rejection
- Display rejection timeline entry with category badge

**Timeline Display:**
- Show REJECTED events with category badges
- Display reason text in timeline note
- Maintain chronological ordering

## User Flow

### Primary Flow: Pipeline Move to Rejected

1. User drags application to "Rejected" stage in pipeline
2. Dialog appears with stage change confirmation
3. **NEW:** Rejection reason section appears:
   - Category dropdown (optional)
   - Free-text reason field (optional)
4. User can either:
   - Skip rejection reason capture
   - Select category only
   - Select category + add reason text
5. On confirmation:
   - Application status updates to rejected
   - REJECTED timeline event created with rejection details
   - Rejection reason synced to applications table

### Secondary Flow: Edit Rejection Reasons

1. User opens application workspace for rejected application
2. **NEW:** Rejection details section shows current rejection info
3. User can edit category and/or reason text
4. Changes update:
   - Existing REJECTED timeline event
   - Applications table rejection fields
   - Timeline display updates immediately

### Display Flow: Timeline Integration

1. Timeline shows REJECTED event with:
   - Category badge (color-coded)
   - Summary: "Rejected — [Category Name]"
   - Note: Free-text rejection reason (if provided)
2. Category badges use consistent color scheme
3. Hover shows full rejection details

## Technical Requirements

### Backend

**TimelineEvent Model Updates:**
```python
class TimelineEvent(UUIDPrimaryKey, TimestampMixin, Base):
    # Existing fields...
    rejection_reason_category: Mapped[str | None] = mapped_column(
        rejection_reason_category,  # Reuse existing enum
        nullable=True
    )
```

**Service Layer:**
- Update `create_event` to handle rejection category
- Ensure REJECTED events can be updated
- Add `update_rejection_reason` method

**API Endpoints:**
- Timeline events API already supports category field
- No new endpoints needed

### Frontend

**TypeScript Types:**
```typescript
interface TimelineEvent {
  // Existing fields...
  rejection_reason_category?: RejectionReasonCategory;
}

type RejectionReasonCategory =
  | "visa_sponsorship"
  | "lack_of_experience"
  | "salary"
  | "culture_fit"
  | "position_filled"
  | "no_feedback"
  | "other";
```

**Component Changes:**
- Pipeline move dialog: Add rejection capture section
- Application workspace: Add rejection details section
- Timeline display: Add category badge rendering
- Existing timeline event components need minor updates

## Success Criteria

- ✅ Users can capture rejection reasons when moving to Rejected stage (optional)
- ✅ Users can edit rejection reasons in application workspace
- ✅ Rejection reasons display in timeline with category badges
- ✅ Dedicated rejection section in workspace for rejected applications
- ✅ Backward compatible (no breaking changes to existing data)
- ✅ Performance: No significant impact on pipeline moves or timeline loading
- ✅ Accessibility: Rejection reason capture follows existing a11y patterns
- ✅ Analytics ready: Rejection reasons queryable via timeline events

## Edge Cases & Considerations

**Optional Capture:**
- Users can skip rejection reason entirely
- Category can be selected without reason text
- Reason text can be provided without category (fallback to "other")

**Timeline Event Updates:**
- REJECTED events should be editable (unlike most timeline events)
- Need to handle multiple REJECTED events (use most recent)
- Maintain event history for audit trail

**Category Enum:**
- Use existing enum from applications table
- No user-defined categories in this scope
- Future-proof for potential category expansion

**Display Consistency:**
- Category badges use consistent colors
- Timeline and workspace show same information
- Empty rejection state handled gracefully

## Testing Strategy

**Backend Tests:**
- Timeline event creation with rejection category
- REJECTED event update functionality
- Rejection reason sync to applications table
- Timeline event queries with rejection filtering

**Frontend Tests:**
- Pipeline move dialog rejection capture
- Workspace rejection details editing
- Timeline category badge rendering
- Optional capture scenarios

**Integration Tests:**
- End-to-end rejection flow (pipeline → timeline → workspace)
- Multiple REJECTED events handling
- Analytics queries on rejection reasons

## Dependencies

**Blocks:**
- None (builds on completed F2 timeline events)

**Unblocks:**
- F4 New default pipeline (if needed)
- Analytics enhancements (rejection reason breakdowns)
- Potential future features (follow-up suggestions based on rejection patterns)

## Migration & Rollout

**Database Migration:**
- Add `rejection_reason_category` column to timeline_events table
- Update existing REJECTED events where possible
- No data loss expected

**Feature Rollout:**
- Backend deployment first (API compatible)
- Frontend deployment second (UI enhancements)
- No user action required (feature is additive)

## Performance Considerations

**Query Impact:**
- Timeline queries may include rejection category filtering
- Minimal impact (additional nullable field)
- Existing indexes support new queries

**UI Performance:**
- Category badges: CSS-based, minimal rendering cost
- Rejection details section: Only loads for rejected applications
- No N+1 queries expected

## Future Enhancements (Out of Scope)

- Analytics dashboard with rejection reason breakdowns
- Follow-up suggestions based on rejection patterns
- Custom rejection categories (beyond enum)
- Rejection reason trends over time
- Export rejection data for analysis

---

**Status:** Ready for implementation planning
**Approve:** Get user approval before proceeding to implementation plan
**Next Step:** Invoke writing-plans skill to create detailed implementation plan