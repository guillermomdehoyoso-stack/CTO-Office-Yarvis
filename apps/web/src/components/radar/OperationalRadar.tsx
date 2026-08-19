import { Navigate } from 'react-router-dom';

/** Legacy Radar bookmarks resolve to the tenant-scoped Netpay Inbox. */
export function OperationalRadar() {
  return <Navigate to="/netpay-inbox" replace />;
}
