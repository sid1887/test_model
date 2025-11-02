import * as React from "react"
import { cn } from "@/lib/utils"

const AetherTable = React.forwardRef<
  HTMLTableElement,
  React.HTMLAttributes<HTMLTableElement>
>(({ className, ...props }, ref) => (
  <div className="relative w-full overflow-auto">
    <table
      ref={ref}
      className={cn("w-full caption-bottom text-sm", className)}
      {...props}
    />
  </div>
))
AetherTable.displayName = "AetherTable"

const AetherTableHeader = React.forwardRef<
  HTMLTableSectionElement,
  React.HTMLAttributes<HTMLTableSectionElement>
>(({ className, ...props }, ref) => (
  <thead 
    ref={ref} 
    className={cn(
      "bg-gradient-to-r from-aether-primary/10 to-aether-glow/10 backdrop-blur-sm border-b border-aether-glow/20",
      className
    )} 
    {...props} 
  />
))
AetherTableHeader.displayName = "AetherTableHeader"

const AetherTableBody = React.forwardRef<
  HTMLTableSectionElement,
  React.HTMLAttributes<HTMLTableSectionElement>
>(({ className, ...props }, ref) => (
  <tbody
    ref={ref}
    className={cn("[&_tr:last-child]:border-0", className)}
    {...props}
  />
))
AetherTableBody.displayName = "AetherTableBody"

const AetherTableFooter = React.forwardRef<
  HTMLTableSectionElement,
  React.HTMLAttributes<HTMLTableSectionElement>
>(({ className, ...props }, ref) => (
  <tfoot
    ref={ref}
    className={cn(
      "border-t bg-gradient-to-r from-aether-primary/5 to-aether-glow/5 font-medium [&>tr]:last:border-b-0",
      className
    )}
    {...props}
  />
))
AetherTableFooter.displayName = "AetherTableFooter"

const AetherTableRow = React.forwardRef<
  HTMLTableRowElement,
  React.HTMLAttributes<HTMLTableRowElement>
>(({ className, ...props }, ref) => (
  <tr
    ref={ref}
    className={cn(
      "border-b border-border/50 transition-all duration-200 hover:bg-aether-primary/5 data-[state=selected]:bg-aether-glow/10",
      className
    )}
    {...props}
  />
))
AetherTableRow.displayName = "AetherTableRow"

const AetherTableHead = React.forwardRef<
  HTMLTableCellElement,
  React.ThHTMLAttributes<HTMLTableCellElement>
>(({ className, ...props }, ref) => (
  <th
    ref={ref}
    className={cn(
      "h-12 px-4 text-left align-middle font-semibold text-foreground [&:has([role=checkbox])]:pr-0 bg-gradient-to-r from-aether-primary to-aether-glow bg-clip-text text-transparent",
      className
    )}
    {...props}
  />
))
AetherTableHead.displayName = "AetherTableHead"

const AetherTableCell = React.forwardRef<
  HTMLTableCellElement,
  React.TdHTMLAttributes<HTMLTableCellElement>
>(({ className, ...props }, ref) => (
  <td
    ref={ref}
    className={cn("p-4 align-middle [&:has([role=checkbox])]:pr-0", className)}
    {...props}
  />
))
AetherTableCell.displayName = "AetherTableCell"

const AetherTableCaption = React.forwardRef<
  HTMLTableCaptionElement,
  React.HTMLAttributes<HTMLTableCaptionElement>
>(({ className, ...props }, ref) => (
  <caption
    ref={ref}
    className={cn("mt-4 text-sm text-muted-foreground", className)}
    {...props}
  />
))
AetherTableCaption.displayName = "AetherTableCaption"

export {
  AetherTable,
  AetherTableHeader,
  AetherTableBody,
  AetherTableFooter,
  AetherTableHead,
  AetherTableRow,
  AetherTableCell,
  AetherTableCaption,
}
