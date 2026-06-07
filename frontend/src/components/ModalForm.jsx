import React from 'react'

export default function ModalForm({
  open,
  onClose,
  title,
  children,
  onSubmit,
  submitText = '保存',
  cancelText = '取消',
  submitDisabled = false,
  maxWidth,
  hideFooter = false,
  footerLeft,
}) {
  if (!open) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal"
        style={maxWidth ? { maxWidth } : undefined}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h3>{title}</h3>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        {onSubmit ? (
          <form onSubmit={onSubmit}>
            <div className="modal-body">{children}</div>
            {!hideFooter && (
              <div className="modal-footer">
                {footerLeft}
                <button type="button" className="btn btn-secondary" onClick={onClose}>
                  {cancelText}
                </button>
                <button type="submit" className="btn btn-primary" disabled={submitDisabled}>
                  {submitText}
                </button>
              </div>
            )}
          </form>
        ) : (
          <>
            <div className="modal-body">{children}</div>
            {!hideFooter && (
              <div className="modal-footer">
                {footerLeft}
                <button type="button" className="btn btn-secondary" onClick={onClose}>
                  {cancelText}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
