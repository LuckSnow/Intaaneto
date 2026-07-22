import { cloneElement, isValidElement } from 'react'
import { Link } from 'react-router-dom'

import logoFull from '../../assets/images/logo-full.png'

export default function AuthLayout({ children }) {
  const content = isValidElement(children)
    ? cloneElement(
        children,
        {
          className: `${children.props.className || ''} relative`,
        },
        children.props.children,
        <Link
          to="/"
          className="absolute right-5 top-5 z-30 block rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950 sm:right-7 sm:top-7"
          aria-label="Về trang chủ Intaaneto"
        >
          <img
            src={logoFull}
            alt="Intaaneto"
            className="h-9 w-auto object-contain drop-shadow-md sm:h-11"
          />
        </Link>,
      )
    : children

  return (
    <div className="auth-page relative min-h-screen overflow-x-hidden bg-slate-950">
      <div
        className="fixed inset-0 bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: 'url(/images/background2.png)' }}
        aria-hidden="true"
      />

      <main className="relative z-10 flex min-h-screen items-center justify-center px-4 py-8 sm:px-6 sm:py-10 lg:px-8">
        {content}
      </main>
    </div>
  )
}
