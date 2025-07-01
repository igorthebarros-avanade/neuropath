import 'remixicon/fonts/remixicon.css'
import type { Metadata } from "next"
import "./globals.css"
import Header from "../components/layout/Header";
import NextTopLoader from 'nextjs-toploader';

export const metadata: Metadata = {
  title: "Neuro Path"
}

const body = `bg-radial from-70% from-a-darkGray min-h-screen to-[#111]`
const main = `m-auto max-w-[888px] px-8 py-4`

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={body}>
        <NextTopLoader color="var(--color-a-darkOrange)" height={2} showSpinner={false}/>

        <Header/>

        <main className={main}>
          {children}
        </main>
      </body>
    </html>
  )
}
